# AuctionHammer 0.9.43 - stable Windows PowerShell 5.1 compatible launcher.
# Runs from the original URUCHOM_AUCTIONHAMMER.bat without Python or Git.
# The extracted legacy EXE is never modified: new versions live side-by-side.
[CmdletBinding()]
param(
    [switch]$SkipUpdate,
    [switch]$NoLaunch,
    [switch]$Rollback,
    [string]$PackagePath,
    [string]$ChecksumPath,
    [string]$VersionTag,
    [string]$ProjectRoot,
    [switch]$TestFailBeforeActivation
)
$ErrorActionPreference = 'Stop'
$project = if ($ProjectRoot) { [IO.Path]::GetFullPath($ProjectRoot) } else {
    (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
}
$versions = Join-Path $project '.auctionhammer-versions'
$activeFile = Join-Path $project 'ACTIVE_RELEASE.txt'
$previousFile = Join-Path $project 'PREVIOUS_RELEASE.txt'
$legacyExe = Join-Path $project 'AuctionHammer.exe'
$releaseApi = 'https://api.github.com/repos/MateuszBock0/AuctionHammer/releases/latest'
$releasePage = 'https://github.com/MateuszBock0/AuctionHammer/releases/latest'
$headers = @{ 'User-Agent' = 'AuctionHammer-PortableLauncher/0.9.43'; 'Accept'='application/vnd.github+json' }

function Read-VersionPointer([string]$path) {
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { return '' }
    $value = (Get-Content -LiteralPath $path -Raw).Trim()
    if ($value -eq 'legacy') { return 'legacy' }
    if ($value -notmatch '^build-[0-9a-fA-F]{8}$') { return '' }
    return $value.ToLowerInvariant()
}

function Legacy-BuildTag {
    $stamp = Join-Path $project 'BUILD_VERSION.txt'
    if ((Test-Path -LiteralPath $legacyExe -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $project '_internal') -PathType Container) -and
        (Test-Path -LiteralPath $stamp -PathType Leaf)) {
        return (Read-VersionPointer $stamp)
    }
    return ''
}

function Installed-Exe([string]$tag) {
    if ($tag -notmatch '^build-[0-9a-f]{8}$') { return $null }
    $dir = Join-Path $versions $tag
    $candidate = Join-Path $dir 'AuctionHammer.exe'
    $stamp = Join-Path $dir 'BUILD_VERSION.txt'
    if ((Test-Path -LiteralPath $candidate -PathType Leaf) -and
        (Test-Path -LiteralPath (Join-Path $dir '_internal') -PathType Container) -and
        (Test-Path -LiteralPath $stamp -PathType Leaf) -and
        ((Get-Content -LiteralPath $stamp -Raw).Trim().ToLowerInvariant() -eq $tag)) {
        return $candidate
    }
    return $null
}

function Current-Exe {
    $tag = Read-VersionPointer $activeFile
    if ($tag -eq 'legacy' -and (Test-Path -LiteralPath $legacyExe -PathType Leaf)) {
        Write-Host '[Rollback] Original portable release selected.'
        return $legacyExe
    }
    $path = Installed-Exe $tag
    if ($path) { return $path }
    $prior = Installed-Exe (Read-VersionPointer $previousFile)
    if ($prior) {
        Write-Host '[Rollback] Current version unavailable; using previous validated release.'
        return $prior
    }
    if (Test-Path -LiteralPath $legacyExe -PathType Leaf) {
        Write-Host '[Offline] Using existing portable AuctionHammer.exe.'
        return $legacyExe
    }
    return $null
}

function Atomic-WritePointer([string]$destination,[string]$tag) {
    if ($tag -ne 'legacy' -and $tag -notmatch '^build-[0-9a-f]{8}$') {
        throw "Invalid release tag: $tag"
    }
    $temp = Join-Path $project ('.auctionhammer-pointer-' + [Guid]::NewGuid().ToString('N') + '.tmp')
    try {
        [IO.File]::WriteAllText($temp,$tag,[Text.Encoding]::ASCII)
        if (Test-Path -LiteralPath $destination -PathType Leaf) {
            # .NET Framework/Windows PowerShell 5.1 requires a valid backup path.
            # Both files are on the same volume; Replace is atomic on NTFS.
            $backup = Join-Path $project ('.auctionhammer-pointer-' + [Guid]::NewGuid().ToString('N') + '.bak')
            [IO.File]::Replace($temp,$destination,$backup)
            if (Test-Path -LiteralPath $backup) {
                Remove-Item -LiteralPath $backup -Force -ErrorAction SilentlyContinue
            }
        } else {
            [IO.File]::Move($temp,$destination)
        }
    } finally {
        if (Test-Path -LiteralPath $temp) { Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue }
    }
}

function Valid-ReleasePayload([string]$dir,[string]$tag) {
    if (-not (Test-Path -LiteralPath (Join-Path $dir 'AuctionHammer.exe') -PathType Leaf)) {
        throw 'Downloaded release is missing AuctionHammer.exe.'
    }
    if (-not (Test-Path -LiteralPath (Join-Path $dir '_internal') -PathType Container)) {
        throw 'Downloaded release is missing PyInstaller _internal.'
    }
    foreach ($required in @('VERSION.json','BUILD_VERSION.txt','URUCHOM_AUCTIONHAMMER.bat')) {
        if (-not (Test-Path -LiteralPath (Join-Path $dir $required) -PathType Leaf)) {
            throw ('Downloaded release is missing ' + $required)
        }
    }
    $stamp = (Get-Content -LiteralPath (Join-Path $dir 'BUILD_VERSION.txt') -Raw).Trim().ToLowerInvariant()
    if ($stamp -ne $tag) { throw ('BUILD_VERSION.txt mismatch: ' + $stamp + ' vs ' + $tag) }
    $meta = Get-Content -LiteralPath (Join-Path $dir 'VERSION.json') -Raw | ConvertFrom-Json
    if (-not $meta.mvp -or [string]$meta.app -ne 'AuctionHammer') {
        throw 'Malformed VERSION.json in downloaded release.'
    }
    if ((Get-Item -LiteralPath (Join-Path $dir 'AuctionHammer.exe')).Length -lt 10000) {
        throw 'Downloaded EXE is unexpectedly small.'
    }
}

function Verify-Archive([string]$archive,[string]$checksum) {
    if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) { throw 'Release archive was not downloaded.' }
    if (-not (Test-Path -LiteralPath $checksum -PathType Leaf)) { throw 'Missing release SHA256 checksum.' }
    $line = (Get-Content -LiteralPath $checksum -Raw).Trim()
    $match = [regex]::Match($line,'^(?<hash>[0-9a-fA-F]{64})\s+\*?AuctionHammer-Windows\.zip\s*$')
    if (-not $match.Success) { throw 'Invalid checksum file (requires SHA256 and filename).' }
    $expected = $match.Groups['hash'].Value.ToUpperInvariant()
    $actual = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToUpperInvariant()
    if ($actual -ne $expected) { throw "SHA256 mismatch: download is corrupt." }
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $zip = [IO.Compression.ZipFile]::OpenRead($archive)
    try {
        $files = @($zip.Entries)
        if ($files.Count -lt 5) { throw 'ZIP has too few entries.' }
        foreach ($entry in $files) {
            $name = $entry.FullName.Replace('\','/')
            if ($name.StartsWith('/') -or
                -not $name.StartsWith('AuctionHammer/') -or
                $name.Contains('../') -or $name.Contains('/./') -or
                $name.Contains(':')) {
                throw ('Unsafe ZIP entry: ' + $name)
            }
        }
    } finally { $zip.Dispose() }
}

function Install-Version([string]$archive,[string]$checksum,[string]$tag) {
    if ($tag -notmatch '^build-[0-9a-fA-F]{8}$') { throw 'Unsafe/invalid release tag.' }
    $tag = $tag.ToLowerInvariant()
    if (-not (Test-Path -LiteralPath $versions)) {
        New-Item -Path $versions -ItemType Directory -Force | Out-Null
    }
    $staging = Join-Path $versions ('.staging-' + [Guid]::NewGuid().ToString('N'))
    $destination = Join-Path $versions $tag
    New-Item -Path $staging -ItemType Directory -Force | Out-Null
    $installed = $false
    try {
        $localArchive = Join-Path $staging 'AuctionHammer-Windows.zip'
        $localChecksum = Join-Path $staging 'AuctionHammer-Windows.zip.sha256'
        Copy-Item -LiteralPath $archive -Destination $localArchive
        Copy-Item -LiteralPath $checksum -Destination $localChecksum
        Verify-Archive $localArchive $localChecksum
        Write-Host '[Aktualizacja] SHA256 verified. Extracting safely...'
        $unpacked = Join-Path $staging 'unpacked'
        Expand-Archive -LiteralPath $localArchive -DestinationPath $unpacked
        $incoming = Join-Path $unpacked 'AuctionHammer'
        Valid-ReleasePayload $incoming $tag
        if ($TestFailBeforeActivation) { throw '[QA] Simulated interruption before activation.' }
        if (-not (Test-Path -LiteralPath $destination)) {
            # Both paths are on the SAME volume. Rename folder only after full validation.
            Move-Item -LiteralPath $incoming -Destination $destination
        } else {
            Valid-ReleasePayload $destination $tag
        }
        $old = Read-VersionPointer $activeFile
        if (-not $old -and (Test-Path -LiteralPath $legacyExe -PathType Leaf)) {
            $old = 'legacy'
        }
        if ($old -and $old -ne $tag -and
            (($old -eq 'legacy' -and (Test-Path -LiteralPath $legacyExe -PathType Leaf)) -or
             (Installed-Exe $old))) {
            Atomic-WritePointer $previousFile $old
        }
        # One tiny atomic pointer swap. No in-place overwrites of the old EXE.
        Atomic-WritePointer $activeFile $tag
        $installed = $true
        Write-Host ('[Aktualizacja] Activated ' + $tag + ' (old version kept for rollback).')
    } finally {
        if (Test-Path -LiteralPath $staging) {
            Remove-Item -LiteralPath $staging -Recurse -Force -ErrorAction SilentlyContinue
        }
        if (-not $installed) { Write-Host '[Aktualizacja] Previous version and pointer remain unchanged.' }
    }
}

function Start-Installed {
    $target = Current-Exe
    if (-not $target) {
        Write-Host '[Brak EXE] No runnable release. Connect to the Internet, then retry.'
        Write-Host $releasePage
        return 2
    }
    Write-Host ('[Start] ' + $target)
    if ($NoLaunch) { return 0 }
    $process = Start-Process -FilePath $target -WorkingDirectory (Split-Path -Parent $target) -Wait -PassThru
    return [int]$process.ExitCode
}

# Prevent simultaneous activations when the user double-clicks the BAT twice.
$mutex = [System.Threading.Mutex]::new($false,'Local\AuctionHammerPortableUpdater')
$locked = $false
try {
    $locked = $mutex.WaitOne(15000)
    if (-not $locked) {
        Write-Host '[Aktualizacja] Another launcher is busy. Starting the installed version.'
        exit (Start-Installed)
    }
    if ($Rollback) {
        $prior = Read-VersionPointer $previousFile
        if (-not (($prior -eq 'legacy' -and
                    (Test-Path -LiteralPath $legacyExe -PathType Leaf)) -or
                   (Installed-Exe $prior))) {
            Write-Host '[Rollback] No previous verified version is available.'
            exit 3
        }
        $now = Read-VersionPointer $activeFile
        if ($now -and (Installed-Exe $now)) { Atomic-WritePointer $previousFile $now }
        Atomic-WritePointer $activeFile $prior
        Write-Host ('[Rollback] Restored ' + $prior)
        exit (Start-Installed)
    }
    if (-not $SkipUpdate) {
        $tag = ''
        $archive = $PackagePath
        $checksum = $ChecksumPath
        try {
            if ($PackagePath -or $ChecksumPath -or $VersionTag) {
                if (-not ($PackagePath -and $ChecksumPath -and $VersionTag)) {
                    throw 'Local installation requires -PackagePath, -ChecksumPath and -VersionTag together.'
                }
                $tag = $VersionTag
            } else {
                Write-Host '[GitHub] Checking for the latest Windows release (7 s timeout)...'
                $latest = Invoke-RestMethod -Uri $releaseApi -Headers $headers -TimeoutSec 7
                $tag = [string]$latest.tag_name
                if ($tag -notmatch '^build-[0-9a-fA-F]{8}$') { throw 'Unknown release tag format.' }
                if ((Legacy-BuildTag) -eq $tag -and
                    (-not (Read-VersionPointer $activeFile) -or
                     (Read-VersionPointer $activeFile) -eq 'legacy')) {
                    Write-Host '[Aktualizacja] This extracted Windows ZIP already contains the latest release.'
                    $archive = ''
                } elseif (Installed-Exe $tag) {
                    $current = Read-VersionPointer $activeFile
                    if ($current -ne $tag) {
                        if ($current -and (Installed-Exe $current)) {
                            Atomic-WritePointer $previousFile $current
                        } elseif ($current -eq 'legacy' -or
                                  (Test-Path -LiteralPath $legacyExe -PathType Leaf)) {
                            Atomic-WritePointer $previousFile 'legacy'
                        }
                        Atomic-WritePointer $activeFile $tag
                    }
                    Write-Host '[Aktualizacja] Verified version already installed locally.'
                    $archive = ''
                } else {
                    $zipAsset = $latest.assets | Where-Object { $_.name -eq 'AuctionHammer-Windows.zip' } | Select-Object -First 1
                    $sumAsset = $latest.assets | Where-Object { $_.name -eq 'AuctionHammer-Windows.zip.sha256' } | Select-Object -First 1
                    if (-not $zipAsset -or -not $sumAsset) {
                        throw 'Latest release has no SHA256 manifest. Keeping installed version.'
                    }
                    $download = Join-Path ([IO.Path]::GetTempPath()) ('AuctionHammer-fetch-' + [Guid]::NewGuid().ToString('N'))
                    New-Item -ItemType Directory -Path $download | Out-Null
                    $archive = Join-Path $download 'AuctionHammer-Windows.zip'
                    $checksum = Join-Path $download 'AuctionHammer-Windows.zip.sha256'
                    Write-Host ('[Aktualizacja] Downloading verified package ' + $tag)
                    Invoke-WebRequest -Uri ([string]$sumAsset.browser_download_url) -Headers $headers -TimeoutSec 30 -OutFile $checksum
                    Invoke-WebRequest -Uri ([string]$zipAsset.browser_download_url) -Headers $headers -TimeoutSec 180 -OutFile $archive
                }
            }
            if ($archive) {
                if ((Read-VersionPointer $activeFile) -eq $tag -and (Installed-Exe $tag)) {
                    Write-Host '[Aktualizacja] Already up to date.'
                } else {
                    Install-Version $archive $checksum $tag
                }
            }
        } catch {
            Write-Host ('[Aktualizacja] ' + $_.Exception.Message)
            Write-Host '[Aktualizacja] Starting the existing version; no partial installation activated.'
        } finally {
            if ($download -and (Test-Path -LiteralPath $download)) {
                Remove-Item -LiteralPath $download -Recurse -Force -ErrorAction SilentlyContinue
            }
        }
    }
    exit (Start-Installed)
} finally {
    if ($locked) { $mutex.ReleaseMutex() }
    $mutex.Dispose()
}

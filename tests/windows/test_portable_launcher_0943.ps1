# Windows PowerShell 5.1 acceptance for 0.9.43 launcher.
# Uses local synthetic releases only; no network, Python, Git or GUI.
$ErrorActionPreference = 'Stop'
$root = (Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$launcher = Join-Path $root 'tools/portable_launcher.ps1'
$work = Join-Path ([IO.Path]::GetTempPath()) ('AuctionHammer-qa0943-' + [Guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $work -Force | Out-Null

function Assert-True([bool]$condition,[string]$reason) {
    if (-not $condition) { throw ("0.9.43 acceptance FAIL: " + $reason) }
}
function Make-MockRelease([string]$tag,[switch]$NoExe,[switch]$InvalidArchive) {
    $rootFolder = Join-Path $work ('source-' + $tag + '-' + [Guid]::NewGuid().ToString('N'))
    $payload = Join-Path $rootFolder 'AuctionHammer'
    New-Item -ItemType Directory -Path $payload -Force | Out-Null
    New-Item -ItemType Directory -Path (Join-Path $payload '_internal') -Force | Out-Null
    [IO.File]::WriteAllText((Join-Path $payload '_internal/ready.txt'),'ready')
    if (-not $NoExe) {
        [IO.File]::WriteAllBytes((Join-Path $payload 'AuctionHammer.exe'),(New-Object byte[] 16000))
    }
    [IO.File]::WriteAllText((Join-Path $payload 'BUILD_VERSION.txt'),$tag)
    [IO.File]::WriteAllText((Join-Path $payload 'VERSION.json'),'{"app":"AuctionHammer","mvp":"0.9.43"}')
    [IO.File]::WriteAllText((Join-Path $payload 'URUCHOM_AUCTIONHAMMER.bat'),'@echo off')
    $archive = Join-Path $rootFolder 'AuctionHammer-Windows.zip'
    if ($InvalidArchive) {
        [IO.File]::WriteAllText($archive,'not a zip')
    } else {
        Compress-Archive -Path $payload -DestinationPath $archive -Force
    }
    $sum = Join-Path $rootFolder 'AuctionHammer-Windows.zip.sha256'
    $hash = (Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant()
    [IO.File]::WriteAllText($sum,($hash + ' *AuctionHammer-Windows.zip'),[Text.Encoding]::ASCII)
    return @{ archive=$archive; checksum=$sum; tag=$tag }
}
function Invoke-QA([string]$install,[hashtable]$release,[string[]]$extra=@(),[int]$expected=0) {
    $argv = @('-NoProfile','-ExecutionPolicy','Bypass','-File',$launcher,
               '-ProjectRoot',$install,'-NoLaunch')
    if ($release) {
        $argv += @('-PackagePath',$release.archive,'-ChecksumPath',$release.checksum,
                   '-VersionTag',$release.tag)
    } else {
        $argv += @('-SkipUpdate')
    }
    $argv += $extra
    $output = & powershell.exe @argv 2>&1 | Out-String
    $status = $LASTEXITCODE
    if ($status -ne $expected) {
        throw "Launcher exited $status (expected $expected): $output"
    }
    return $output
}
function Read-Active([string]$install) {
    $marker = Join-Path $install 'ACTIVE_RELEASE.txt'
    if (Test-Path -LiteralPath $marker) { return (Get-Content -LiteralPath $marker -Raw).Trim() }
    return ''
}
try {
    $install = Join-Path $work 'existing-install'
    New-Item -ItemType Directory -Path $install -Force | Out-Null
    $legacy = Join-Path $install 'AuctionHammer.exe'
    [IO.File]::WriteAllText($legacy,'original-legacy-exe')
    [IO.File]::WriteAllText((Join-Path $install 'important-user-file.txt'),'do-not-touch')
    $old = (Get-FileHash -LiteralPath $legacy -Algorithm SHA256).Hash
    $first = Make-MockRelease 'build-1111aaaa'
    $second = Make-MockRelease 'build-2222bbbb'
    $third = Make-MockRelease 'build-3333cccc'
    $fourth = Make-MockRelease 'build-4444dddd' -NoExe
    $notZip = Make-MockRelease 'build-5555eeee' -InvalidArchive

    # First install never modifies the legacy executable.
    Invoke-QA $install $first | Out-Null
    Assert-True ((Read-Active $install) -eq $first.tag) 'First activation'
    Assert-True ((Get-FileHash -LiteralPath $legacy -Algorithm SHA256).Hash -eq $old) 'Legacy EXE was overwritten'
    Assert-True ((Test-Path -LiteralPath (Join-Path $install ".auctionhammer-versions/$($first.tag)/_internal"))) 'Missing bundled runtime'

    # A second verified version is deployed alongside the first.
    Invoke-QA $install $second | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'Second activation'
    Assert-True (((Get-Content (Join-Path $install 'PREVIOUS_RELEASE.txt') -Raw).Trim()) -eq $first.tag) 'Previous release pointer'
    Assert-True ((Test-Path -LiteralPath (Join-Path $install ".auctionhammer-versions/$($first.tag)/AuctionHammer.exe"))) 'Rollback binary lost'

    # Simulate interrupted installation after validation but before pointer.
    Invoke-QA $install $third @('-TestFailBeforeActivation') | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'Interrupted update switched active version'
    Assert-True (@(Get-ChildItem -LiteralPath (Join-Path $install '.auctionhammer-versions') -Filter '.staging-*').Count -eq 0) 'Staging was left behind'

    # SHA mismatch must NEVER switch the pointer.
    $tampered = Make-MockRelease 'build-6666ffff'
    Add-Content -LiteralPath $tampered.archive -Value 'tampered'
    Invoke-QA $install $tampered | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'SHA mismatch activated corrupt ZIP'

    # Even with matching SHA, structurally invalid ZIP cannot activate.
    Invoke-QA $install $notZip | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'Invalid archive activated'

    # Structurally valid package without an EXE cannot activate.
    Invoke-QA $install $fourth | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'Incomplete package activated'

    # Offline operation must not contact GitHub. Rollback is explicit.
    Invoke-QA $install $null | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'Offline changed the release pointer'
    Invoke-QA $install $null @('-Rollback') | Out-Null
    Assert-True ((Read-Active $install) -eq $first.tag) 'Rollback failed'
    Invoke-QA $install $null @('-Rollback') | Out-Null
    Assert-True ((Read-Active $install) -eq $second.tag) 'Rollback reverse failed'

    # Empty or source-only installs cannot claim success offline.
    $empty = Join-Path $work 'empty'
    New-Item -Path $empty -ItemType Directory | Out-Null
    Invoke-QA $empty $null @() 2 | Out-Null

    # File blocking creation simulates permissions/space errors without admin ACLs.
    $blocked = Join-Path $work 'unwritable-install'
    New-Item -Path $blocked -ItemType Directory | Out-Null
    [IO.File]::WriteAllText((Join-Path $blocked 'AuctionHammer.exe'),'old')
    [IO.File]::WriteAllText((Join-Path $blocked '.auctionhammer-versions'),'not a directory')
    Invoke-QA $blocked $first | Out-Null
    Assert-True ((Read-Active $blocked) -eq '') 'Storage failure activated incomplete install'

    Assert-True ((Get-Content (Join-Path $install 'important-user-file.txt') -Raw).Trim() -eq 'do-not-touch') 'User file changed'
    Assert-True ((Get-FileHash -LiteralPath $legacy -Algorithm SHA256).Hash -eq $old) 'Legacy EXE modified after rollback'
    Write-Host '0.9.43 QA: PASS (version switching, SHA256, corrupt ZIP, rollback, offline, storage failure, legacy safety)'
} finally {
    if (Test-Path -LiteralPath $work) {
        Remove-Item -LiteralPath $work -Recurse -Force -ErrorAction SilentlyContinue
    }
}

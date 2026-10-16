    # Windows built-in PowerShell. Does not require Python, pip, Git or VS Code.
    $ErrorActionPreference = 'Stop'
    $project = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $exe = Join-Path $project 'AuctionHammer.exe'
    $localBuild = Join-Path $project 'BUILD_VERSION.txt'
    $api = 'https://api.github.com/repos/MateuszBock0/AuctionHammer/releases/latest'
    $releaseUrl = 'https://github.com/MateuszBock0/AuctionHammer/releases/latest'
    $latest = $null
    $headers = @{ 'User-Agent' = 'AuctionHammer-PortableLauncher' }
    try {
        Write-Host '[GitHub] Checking for a newer release (7-second timeout)...'
        $latest = Invoke-RestMethod -Uri $api -Headers $headers -TimeoutSec 7
    } catch {
        Write-Host '[GitHub] Update check unavailable. The installed version can run offline.'
    }
    if ($null -ne $latest) {
        $installed = if(Test-Path $localBuild) {(Get-Content $localBuild -Raw).Trim()} else {''}
        if ($installed -ne [string]$latest.tag_name -or -not (Test-Path $exe)) {
            $asset = $latest.assets | Where-Object { $_.name -eq 'AuctionHammer-Windows.zip' } | Select-Object -First 1
            if ($null -ne $asset) {
                $tmp = Join-Path ([IO.Path]::GetTempPath()) ('AuctionHammer-update-' + [Guid]::NewGuid().ToString('N'))
                New-Item -ItemType Directory -Path $tmp | Out-Null
                $archive = Join-Path $tmp 'update.zip'
                $unpacked = Join-Path $tmp 'unpacked'
                try {
                    Write-Host ('[Aktualizacja] Downloading ' + [string]$latest.tag_name + ' ...')
                    Invoke-WebRequest -Uri ([string]$asset.browser_download_url) -Headers $headers -TimeoutSec 120 -OutFile $archive
                    Expand-Archive -LiteralPath $archive -DestinationPath $unpacked -Force
                    $incoming = Join-Path $unpacked 'AuctionHammer'
                    if (-not (Test-Path (Join-Path $incoming 'AuctionHammer.exe'))) {throw 'The downloaded package is missing AuctionHammer.exe.'}
                    # Update distribution, never touch local Git history or .venv.
                    Get-ChildItem -LiteralPath $incoming -Force | ForEach-Object {
                        if ($_.Name -notin @('.git','.venv')) {
                            Copy-Item -LiteralPath $_.FullName -Destination $project -Recurse -Force
                        }
                    }
                    Write-Host '[Aktualizacja] Update installed.'
                } catch {
                    Write-Host ('[Aktualizacja] Download or installation failed: ' + $_.Exception.Message)
                    Write-Host '[Aktualizacja] Keeping the existing installation.'
                } finally {
                    Remove-Item -LiteralPath $tmp -Recurse -Force -ErrorAction SilentlyContinue
                }
            }
        } else {
            Write-Host '[Aktualizacja] Already up to date.'
        }
    }
    if (-not (Test-Path $exe)) {
        Write-Host '[Brak EXE] Executable not found. Download the latest Windows release or enable Internet access for the updater.'
        Write-Host ('Latest Windows release: ' + $releaseUrl)
        exit 2
    }
    Write-Host '[Start] Launching AuctionHammer.exe'
    Start-Process -FilePath $exe -WorkingDirectory $project -Wait
    exit 0

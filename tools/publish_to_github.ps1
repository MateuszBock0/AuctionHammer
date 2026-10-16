    # One-time publish using existing Git installation; Git Credential Manager prompts in browser.
    $ErrorActionPreference = 'Stop'
    $root = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
    $repoUrl = 'https://github.com/MateuszBock0/AuctionHammer.git'
    $gitCommand = Get-Command git -ErrorAction SilentlyContinue
    $gitExe = if ($gitCommand) { $gitCommand.Source } else {''}
    if (-not $gitExe) {
        $candidates = @('C:\Program Files\Git\cmd\git.exe', 'C:\Program Files\Git\bin\git.exe', (Join-Path $env:LOCALAPPDATA 'Programs\Git\cmd\git.exe'))
        foreach ($candidate in $candidates) {if (Test-Path $candidate) { $gitExe = $candidate; break }}
    }
    if (-not $gitExe) {
        Write-Host '[Git] Nie znaleziono Gita. Na obecnym komputerze masz Git Bash — uruchom instalator tam.'
        Write-Host 'Na nowym komputerze Git nie jest potrzebny do gry: pobierz wersje z Releases.'
        exit 1
    }
    $temp = Join-Path ([IO.Path]::GetTempPath()) ('AuctionHammer-publish-' + [Guid]::NewGuid().ToString('N'))
    New-Item -ItemType Directory -Path $temp | Out-Null
    $clone = Join-Path $temp 'AuctionHammer'
    try {
        Write-Host ('[Git] Pobieram aktualny stan ' + $repoUrl)
        & $gitExe clone --depth 1 $repoUrl $clone
        if ($LASTEXITCODE -ne 0) {throw 'Nie mozna sklonowac repozytorium.'}
        $ignored = @('.git','.venv','__pycache__','.pytest_cache','_internal','dist','build')
        Get-ChildItem -LiteralPath $root -Force | ForEach-Object {
            if ($_.Name -notin $ignored -and $_.Name -ne 'AuctionHammer.exe' -and $_.Name -ne 'BUILD_VERSION.txt') {
                Copy-Item -LiteralPath $_.FullName -Destination $clone -Recurse -Force
            }
        }
        Push-Location $clone
        try {
            & $gitExe add -A
            if ($LASTEXITCODE -ne 0) {throw 'git add nie powiodlo sie.'}
            & $gitExe diff --cached --quiet
            if ($LASTEXITCODE -eq 0) { Write-Host '[Git] Wszystkie pliki sa juz aktualne.'; exit 0 }
            & $gitExe -c 'user.name=MateuszBock0' -c 'user.email=112616750+MateuszBock0@users.noreply.github.com' commit -m 'AuctionHammer: kompletny master, wersja portable i build Windows'
            if ($LASTEXITCODE -ne 0) {throw 'git commit nie powiodl sie.'}
            Write-Host '[Git] Wysylam na GitHub (moze pojawic sie okno logowania)...'
            & $gitExe push origin HEAD:main
            if ($LASTEXITCODE -ne 0) {throw 'git push nie powiodl sie.'}
            Write-Host '[SUKCES] Pliki w repozytorium. GitHub Actions rozpocznie budowanie Windows EXE.'
            Write-Host 'https://github.com/MateuszBock0/AuctionHammer/actions'
        } finally {Pop-Location}
        Start-Process 'https://github.com/MateuszBock0/AuctionHammer/actions'
    } catch {
        Write-Host ('[BLAD] ' + $_.Exception.Message)
        exit 1
    } finally {
        Remove-Item -LiteralPath $temp -Recurse -Force -ErrorAction SilentlyContinue
    }

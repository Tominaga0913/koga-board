# 4つの画面を、それぞれ別のURLで公開する起動スクリプト
# 使い方: start.bat をダブルクリック(またはこのファイルを PowerShell で実行)
# 止めるとき: この画面で Enter を押す(画面を閉じてしまったら stop.bat)

$ErrorActionPreference = "Stop"
Set-Location $PSScriptRoot

# 指定名, ポート, 画面名
$sites = @(
    @{ key = "yatabi"; port = 8601; name = "米多比郵便局" },
    @{ key = "aoyagi"; port = 8602; name = "青柳郵便局" },
    @{ key = "cosmos"; port = 8603; name = "コスモス館" },
    @{ key = "koga";   port = 8604; name = "JR古賀駅 自由通路" }
)

# cloudflared を探す
$cf = (Get-Command cloudflared -ErrorAction SilentlyContinue).Source
if (-not $cf) {
    foreach ($p in @("${env:ProgramFiles(x86)}\cloudflared\cloudflared.exe", "$env:ProgramFiles\cloudflared\cloudflared.exe")) {
        if (Test-Path $p) { $cf = $p }
    }
}
if (-not $cf) {
    Write-Host "cloudflared が見つかりません。先に次を実行してください:" -ForegroundColor Red
    Write-Host "  winget install --id Cloudflare.cloudflared"
    Read-Host "Enter で閉じます"
    exit 1
}

$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$pidFile = Join-Path $logDir "pids.txt"
$appPidFile = Join-Path $logDir "app_pids.txt"   # restart.bat がアプリだけ入れ替えるのに使う
$pids = @()
$appLines = @()

# 前回の start.bat が残っていると、同じ番号(ポート)を使えず古い画面のままになるので、先に止める
$leftover = Get-CimInstance Win32_Process -Filter "name='python.exe' or name='cloudflared.exe'" |
    Where-Object { $_.CommandLine -match 'server\.port 860[1-4]|localhost:860[1-4]' }
if ($leftover) {
    Write-Host "前回の起動が残っていたので止めます($(@($leftover).Count)個)..." -ForegroundColor Yellow
    $leftover | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
}

Write-Host "起動しています..." -ForegroundColor Cyan
foreach ($s in $sites) {
    $st = Start-Process python -PassThru -WindowStyle Hidden `
        -ArgumentList "-m", "streamlit", "run", "app.py", "--server.headless", "true", `
                      "--server.port", "$($s.port)", "--", $s.key `
        -RedirectStandardOutput "$logDir\$($s.key)_app.log" -RedirectStandardError "$logDir\$($s.key)_app.err"
    $tn = Start-Process $cf -PassThru -WindowStyle Hidden `
        -ArgumentList "tunnel", "--url", "http://localhost:$($s.port)" `
        -RedirectStandardOutput "$logDir\$($s.key)_tunnel.log" -RedirectStandardError "$logDir\$($s.key)_tunnel.err"
    $pids += $st.Id, $tn.Id
    $appLines += "$($s.key),$($s.port),$($st.Id)"
}
$pids | Set-Content $pidFile
$appLines | Set-Content $appPidFile

# 各トンネルのURLがログに出るのを待つ(最大60秒)
$urls = @{}
for ($i = 0; $i -lt 60 -and $urls.Count -lt $sites.Count; $i++) {
    Start-Sleep -Seconds 1
    foreach ($s in $sites) {
        if ($urls[$s.key]) { continue }
        $log = "$logDir\$($s.key)_tunnel.err"
        if (Test-Path $log) {
            $m = Select-String -Path $log -Pattern "https://[a-z0-9-]+\.trycloudflare\.com" | Select-Object -First 1
            if ($m) { $urls[$s.key] = $m.Matches[0].Value }
        }
    }
}

$lines = @("コガバス発車標 公開URL($(Get-Date -Format 'yyyy-MM-dd HH:mm') 発行)", "")
Write-Host ""
Write-Host "===== 公開URL =====" -ForegroundColor Green
foreach ($s in $sites) {
    $u = $urls[$s.key]
    if (-not $u) { $u = "(取得できませんでした。logs\$($s.key)_tunnel.err を確認)" }
    Write-Host ("{0,-14} {1}" -f $s.name, $u)
    $lines += "$($s.name): $u"
}
$lines | Set-Content (Join-Path $PSScriptRoot "urls.txt") -Encoding UTF8
Write-Host ""
Write-Host "URLは urls.txt にも保存しました。つながるまで1分ほどかかることがあります。"
Write-Host "この画面は開いたままにしてください。" -ForegroundColor Yellow
Write-Host ""
Read-Host "止めるときは Enter を押してください"

# restart.bat でアプリが入れ替わっていることがあるので、最新の番号も止める
if (Test-Path $appPidFile) {
    Get-Content $appPidFile | ForEach-Object { $pids += [int]($_.Split(",")[2]) }
}
foreach ($id in $pids) { Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
Remove-Item $pidFile, $appPidFile -ErrorAction SilentlyContinue
Write-Host "すべて止めました。"
Start-Sleep -Seconds 2

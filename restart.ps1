# 公開URLはそのままで、発車標のプログラムだけを新しいものに入れ替える
# 使い方: restart.bat をダブルクリック(start.bat の画面は開いたままでよい)

Set-Location $PSScriptRoot
$logDir = Join-Path $PSScriptRoot "logs"
$appPidFile = Join-Path $logDir "app_pids.txt"
$pidFile = Join-Path $logDir "pids.txt"

if (-not (Test-Path $appPidFile)) {
    Write-Host "start.bat が動いていません。先に start.bat を起動してください。" -ForegroundColor Red
    Read-Host "Enter で閉じます"
    exit 1
}

$newLines = @()
foreach ($line in Get-Content $appPidFile) {
    $key, $port, $oldPid = $line.Split(",")
    Stop-Process -Id ([int]$oldPid) -Force -ErrorAction SilentlyContinue
    Start-Sleep -Milliseconds 500
    $st = Start-Process python -PassThru -WindowStyle Hidden `
        -ArgumentList "-m", "streamlit", "run", "app.py", "--server.headless", "true", `
                      "--server.port", $port, "--", $key `
        -RedirectStandardOutput "$logDir\${key}_app.log" -RedirectStandardError "$logDir\${key}_app.err"
    $newLines += "$key,$port,$($st.Id)"
    Write-Host "入れ替えました: $key"
}
$newLines | Set-Content $appPidFile

# stop.bat でも新しいアプリを止められるよう、pids.txt にも追記
if (Test-Path $pidFile) {
    $newLines | ForEach-Object { $_.Split(",")[2] } | Add-Content $pidFile
}

Write-Host ""
Write-Host "完了しました。公開URLは変わっていません。" -ForegroundColor Green
Write-Host "ブラウザやディスプレイの画面は、数秒後に自動でつながり直します(つながらなければ再読み込み)。"
Start-Sleep -Seconds 4

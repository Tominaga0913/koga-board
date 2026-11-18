# ディスプレイ用: Chrome を全画面で開き、「コガバスの発車標」と「西鉄バスナビ(元のページのまま)」を
# 6秒ごとに切り替えて表示する。米多比は西鉄との切り替えがないので、コガバスの画面を全画面で開くだけ。西鉄のページは埋め込まず、URLそのものを開くので一切変更しない。
#
# 使い方: kiosk_yatabi.bat / kiosk_aoyagi.bat / kiosk_cosmos.bat / kiosk_koga.bat をダブルクリック
# 終わるとき: Alt + F4 で Chrome を閉じる(切り替えも自動で止まる)
#
# 仕組み: Chrome を「リモートデバッグ」付きで起動し、2つのタブを開いておいて、
#         http://127.0.0.1:<port>/json/activate/<タブ> で表に出すタブを切り替えている。

param(
    [ValidateSet("yatabi", "aoyagi", "cosmos", "koga")][string]$Site = "aoyagi",
    [string]$BoardUrl = "",      # コガバスの発車標のURL(省略すると urls.txt から探す)
    [int]$Seconds = 6,           # 切り替え間隔(秒)
    [switch]$NoKiosk             # 全画面にしない(動作確認用)
)

# 動作の記録(うまく切り替わらないときの原因調べ用)
$logDir = Join-Path $PSScriptRoot "logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$logFile = Join-Path $logDir "kiosk_$Site.log"
function Log($msg) {
    $line = "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $msg"
    Add-Content $logFile $line -Encoding UTF8
}
Log "---- 起動 ($Site, ${Seconds}秒, kiosk=$(-not $NoKiosk))"

# Chrome との通信(127.0.0.1)は、学校などのプロキシ設定を通さない
[System.Net.WebRequest]::DefaultWebProxy = New-Object System.Net.WebProxy

# 西鉄バスナビ(元のURLのまま)
$nnr = @{
    aoyagi = "https://navi.nnr.co.jp/jikoku/device/busnavi?viewmode=0&cd=0328"
    cosmos = "https://navi.nnr.co.jp/jikoku/device/busnavi?viewmode=0&cd=0322&pos=1"
    koga   = "https://navi.nnr.co.jp/jikoku/device/busnavi?viewmode=0&cd=0321&pos=1"
}
$names = @{ yatabi = "米多比郵便局"; aoyagi = "青柳郵便局"; cosmos = "コスモス館"; koga = "JR古賀駅 自由通路" }
$ports = @{ yatabi = 9321; aoyagi = 9322; cosmos = 9323; koga = 9324 }

# コガバスの発車標のURL: 指定がなければ
#   1. kiosk_urls.txt(サーバーの固定URLを書いておくファイル)
#   2. urls.txt(start.bat が作る、このパソコンから公開したときのURL)
# の順に探す。どちらも「米多比郵便局: https://...」の形で1行ずつ書く。
foreach ($name in "kiosk_urls.txt", "urls.txt") {
    if ($BoardUrl) { break }
    $urlsFile = Join-Path $PSScriptRoot $name
    if (Test-Path $urlsFile) {
        $line = Get-Content $urlsFile -Encoding UTF8 | Where-Object { $_ -like "$($names[$Site]):*" } | Select-Object -First 1
        if ($line) { $BoardUrl = ($line -split ": ", 2)[1].Trim(); Log "URLの読み込み元: $name" }
    }
}
if (-not $BoardUrl -or $BoardUrl -notmatch "^https?://") {
    $BoardUrl = Read-Host "$($names[$Site]) のコガバス発車標のURLを貼り付けて Enter"
}

# 西鉄との切り替えがない場所(米多比)は、全画面で開くだけ
if (-not $nnr[$Site]) {
    $chrome1 = @(
        "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
        "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
        "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
    ) | Where-Object { Test-Path $_ } | Select-Object -First 1
    if (-not $chrome1) { Write-Host "Google Chrome が見つかりません。" -ForegroundColor Red; Read-Host "Enter で閉じます"; exit 1 }
    $profileDir = Join-Path $env:LOCALAPPDATA "koga-board-kiosk\$Site"
    $args1 = @("--user-data-dir=`"$profileDir`"", "--no-first-run", "--no-default-browser-check",
               "--disable-session-crashed-bubble", "--disable-features=Translate")
    if (-not $NoKiosk) { $args1 += "--kiosk" }
    Log "コガバス: $BoardUrl (切り替えなし)"
    Start-Process $chrome1 -ArgumentList ($args1 + $BoardUrl) | Out-Null
    Write-Host "$($names[$Site]) の画面を全画面で開きました。止めるときは Alt + F4 で Chrome を閉じてください。" -ForegroundColor Green
    Start-Sleep -Seconds 3
    exit 0
}
# Chrome を探す
$chrome = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LOCALAPPDATA\Google\Chrome\Application\chrome.exe"
) | Where-Object { Test-Path $_ } | Select-Object -First 1
if (-not $chrome) {
    Write-Host "Google Chrome が見つかりません。" -ForegroundColor Red
    Read-Host "Enter で閉じます"; exit 1
}

# 普段使いの Chrome とは別の設定フォルダで起動する(リモートデバッグに必要)
$port = $ports[$Site]
$profileDir = Join-Path $env:LOCALAPPDATA "koga-board-kiosk\$Site"
$chromeArgs = @(
    "--remote-debugging-port=$port", "--user-data-dir=`"$profileDir`"",
    "--no-first-run", "--no-default-browser-check", "--disable-session-crashed-bubble",
    "--disable-features=Translate",          # 自動翻訳で文字が化けないように
    "--disable-background-timer-throttling", # 裏に回ったタブも更新を止めない
    "--disable-renderer-backgrounding"
)
if (-not $NoKiosk) { $chromeArgs += "--kiosk" }
$chromeArgs += $BoardUrl, $nnr[$Site]

Write-Host "$($names[$Site]): Chrome を起動します..." -ForegroundColor Cyan
Write-Host "  コガバス: $BoardUrl"
Write-Host "  西鉄バス: $($nnr[$Site])"
Log "コガバス: $BoardUrl"
Log "Chrome: $chrome"
$proc = Start-Process $chrome -ArgumentList $chromeArgs -PassThru

$api = "http://127.0.0.1:$port/json"

# 開いているページ(タブ)を探す。Chrome の一覧には内部用の項目(browser_ui など)も
# 混ざるので、type が page で http(s) のものだけを使う。
# ※ Invoke-RestMethod は一覧を1つのまとまりで返すので、変数に入れてから1件ずつ調べる
function Find-Tabs {
    $all = Invoke-RestMethod "$api/list" -TimeoutSec 3
    $pages = @($all | Where-Object { $_.type -eq "page" -and $_.url -match "^https?://" })
    @{
        nnr   = $pages | Where-Object { $_.url -like "*navi.nnr.co.jp*" } | Select-Object -First 1
        board = $pages | Where-Object { $_.url -notlike "*navi.nnr.co.jp*" } | Select-Object -First 1
    }
}

# 2つのタブが開くのを待つ
$boardTab = $null; $nnrTab = $null
for ($i = 0; $i -lt 60 -and -not ($boardTab -and $nnrTab); $i++) {
    Start-Sleep -Milliseconds 500
    try {
        $found = Find-Tabs
        $nnrTab = $found.nnr; $boardTab = $found.board
    } catch { $lastError = $_.Exception.Message }
}
if (-not ($boardTab -and $nnrTab)) {
    Log "タブが見つからない。最後のエラー: $lastError / board=$($found.board.url) nnr=$($found.nnr.url)"
    Write-Host "Chrome のタブを見つけられませんでした。普段の Chrome を一度すべて閉じてから、もう一度試してください。" -ForegroundColor Red
    Read-Host "Enter で閉じます"; exit 1
}

Log "タブ発見: board=$($boardTab.id) nnr=$($nnrTab.id)"
Write-Host "$Seconds 秒ごとに切り替えています。止めるときは Chrome を Alt + F4 で閉じてください。" -ForegroundColor Green
Write-Host "(この黒い画面は閉じないでください。閉じると切り替えが止まります)" -ForegroundColor Yellow
$fails = 0
while ($true) {
    foreach ($which in @("board", "nnr")) {
        # 失敗したら1秒おいてやり直す(10秒待つと同じ画面が20秒続いてしまうため)
        for ($try = 1; $try -le 3; $try++) {
            try {
                # 切り替えのたびにタブを探し直す(1回の取り違えが残らないように)
                $tab = (Find-Tabs)[$which]
                if (-not $tab) { throw "$which のタブが見つかりません" }
                Invoke-RestMethod "$api/activate/$($tab.id)" -TimeoutSec 3 | Out-Null
                $fails = 0
                break
            } catch {
                $fails++
                Log "切り替え失敗($which, $($fails)回目): $($_.Exception.Message)"
                # Chrome が閉じられたかを確認(続けて失敗し、タブ一覧も取れなければ終了)
                $alive = $true
                try { Invoke-RestMethod "$api/list" -TimeoutSec 3 | Out-Null } catch { $alive = $false }
                if (-not $alive -and $fails -ge 2) {
                    Log "Chrome が閉じられたので終了"
                    Write-Host "Chrome が閉じられたので終了します。"; exit 0
                }
                Start-Sleep -Seconds 1
            }
        }
        Start-Sleep -Seconds $Seconds
    }
}

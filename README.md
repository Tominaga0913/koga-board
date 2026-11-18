# コガバス発車標

古賀市内4か所のディスプレイに、コガバスの次の発車を表示するアプリです。
青柳・コスモス館・JR古賀駅では、西鉄バスの「バスナビ」のページ(元のまま、一切変更しない)と6秒ごとに交互に表示します。

| 設置場所 | 内容 | 画面の向き |
|---|---|---|
| 米多比郵便局 | 西鉄バスの古賀駅到着時刻と、乗り継げるJR(博多駅方面・小倉駅方面) | 横長 1980×1280 |
| 青柳郵便局 | コガバス(JR古賀線) ⇔ 西鉄バスナビ(青柳四つ角) | 横長 1980×1280 |
| コスモス館 | コガバス(JR古賀線・小竹線) ⇔ 西鉄バスナビ(コスモス館前) | 縦長 1280×1980 |
| JR古賀駅 自由通路 | コガバス(JR古賀線) ⇔ 西鉄バスナビ(JR古賀駅東口) | 縦長 1280×1980 |

## 使い方(駅員さん・設置する人向け)
GitHub Pages に公開したURLを、ディスプレイにつないだパソコンの Chrome で開くだけです。
軽いページなので開いてすぐ表示され、サーバーの休止もありません。

- 米多比郵便局: https://tominaga0913.github.io/koga-board/yatabi.html
- 青柳郵便局: https://tominaga0913.github.io/koga-board/aoyagi.html
- コスモス館: https://tominaga0913.github.io/koga-board/cosmos.html
- JR古賀駅 自由通路: https://tominaga0913.github.io/koga-board/koga.html

青柳・コスモス館・JR古賀駅は、URLを開くと自動で**表示用のウィンドウ**が開き、コガバスと西鉄バスナビが6秒ごとに入れ替わります。
1. そのパソコンで**最初の1回だけ**、画面の案内に従ってポップアップを「常に許可」にする
2. 表示用のウィンドウで **F11** を押して全画面にする
3. 最初に開いたウィンドウ(「表示中です」と出ているほう)は**閉じない**(閉じると切り替えが止まる)

米多比は切り替えがないので、URLを開いて F11 を押すだけです。

### 長く置いておくときの注意
- パソコンがスリープしたり画面が消えたりしないよう、Windows の電源設定を「なし」にする
- Chrome の設定 →「パフォーマンス」→「常にアクティブにしておくサイト」に `tominaga0913.github.io` を追加する(裏のウィンドウが休止しないように)
- 時刻はパソコンの時計で計算するので、パソコンの時計が正しいこと(Windows の「時刻を自動的に設定する」をオン)

### お知らせを出すとき(遅れ・運休・バス停の移設など)
GitHub のサイトで `docs/notices.txt` を開き、鉛筆マーク(Edit)で1行書いて「Commit changes」。数分で画面の下に黄色い帯で出ます。
```
全部: 本日は道路工事のため、約10分遅れています
青柳、コスモス館: 青柳四ツ角のバス停は、11月30日まで移設しています
```
場所は 全部 / 米多比 / 青柳 / コスモス館 / 古賀駅。消すときはその行を消して Commit します。
### 時刻表を更新したとき(新しいGTFS・米多比のCSV・holidays.csv・config.py を変えたとき)
`python build_pages.py` を動かして `docs/` を作り直してから、GitHub に Push する。数分でページに反映されます。
コガバスの時刻表の期限(今は 2027-03-31)が切れると、画面に「期限が切れています」と出ます。

### GitHub Pages の設定(最初に1回)
1. GitHub のリポジトリを **Public** にする(Settings → 一番下の Danger Zone → Change visibility)
2. Settings → **Pages** → Source を「Deploy from a branch」、Branch を `main` / `/docs` にして Save
## データについて
- **コガバス**: 古賀市が公開しているオープンデータ(GTFS-JP、CC BY 4.0)。`data/` のZIP。画面に出典を表示しています。
  新しいダイヤが出たら https://gtfs-data.jp/ からZIPをダウンロードして `data/` のZIPと入れ替える
- **西鉄バス**: バスナビのページをそのまま開いているだけで、データの読み取りや加工はしていません
- **米多比(JR・西鉄バス)**: 公開データが無いため、手入力のCSVです(下記)。**現在は架空のサンプル時刻**で、画面に「サンプルデータを表示中」と出ます。
  本物の時刻を入れる前に、JR九州・西鉄に時刻表を使ってよいか確認してください

### 米多比の時刻表(手入力CSV)
`data/` に次の2つを作ると、サンプルの代わりに使われます(お知らせの帯も消えます)。
- `data/jr_koga.csv` … JR古賀駅の時刻表
  ```
  方面,ダイヤ,時刻,種別,行き先
  博多方面,平日,6:12,普通,博多
  小倉方面,土休日,6:20,快速,小倉
  ```
- `data/yatabi_bus.csv` … 米多比から古賀駅までの西鉄バス
  ```
  ダイヤ,米多比発,古賀駅着,行き先
  平日,7:10,7:32,JR古賀駅
  ```
- `data/holidays.csv` … 土日以外に「土休日ダイヤ」にする日(祝日・年末年始など)。1行に1日、`YYYY-MM-DD`。
  2026年の祝日を入れてあるので、年が変わったら更新し、バス会社の年末年始ダイヤなども足してください

## 設定(config.py)
- `SWITCH_SECONDS` : コガバス ⇔ 西鉄バス の切り替え秒数(6秒)
- `REFRESH_SECONDS` : 残り時間を計算し直す間隔(15秒)
- `SITES` : 場所ごとの バス停名(`stop`)・路線(`routes`)・西鉄バスナビのURL(`nishitetsu_url`)・向き(`layout`)
- `YATABI` : 米多比の 乗り換え分数(`transfer_minutes`)・方面の表記(`direction_labels`)
- 色を変えるときは `docs/board.css` の `--frame`(今は緑)を書き換える

## プログラムを直したとき
GitHub Desktop で Commit → Push すると、2〜3分でサーバーの4つのアプリが自動で新しくなります。
手元で確かめるときは `python test_departures.py`(テスト)と `streamlit run app.py`(メニュー付きで起動)。

## 予備: Streamlit Community Cloud 版(以前のサーバー)
開くのに数秒かかり、12時間で休止するため、今は GitHub Pages 版を使います。

### サーバーの作り方
1. GitHub にこのフォルダを上げる(`data/` も含める)
2. https://share.streamlit.io に GitHub アカウントでログインし、非公開リポジトリなら Linked accounts で private repos を許可
3. 「Create app」→ リポジトリとブランチ `main`、Main file を下の表のとおり選び、App URL を決めて Deploy(Python 3.11)
4. できたアプリの「Share」で **Public** にする(非公開のアプリは1つしか作れないので、次を作る前に必ず Public にする)
5. 3〜4 を4回くり返す

| 場所 | Main file path |
|---|---|
| 米多比郵便局 | `site_yatabi.py` |
| 青柳郵便局 | `site_aoyagi.py` |
| コスモス館 | `site_cosmos.py` |
| JR古賀駅 自由通路 | `site_koga.py` |

## 予備: 自分のパソコンから公開する(サーバーを使わないとき)
- `start.bat` … 4画面を起動し、Cloudflare Tunnel で一時的なURLを発行(`urls.txt`)。起動するたびにURLが変わる
- `restart.bat` … URLを変えずにプログラムだけ入れ替える / `stop.bat` … すべて止める
- `kiosk_*.bat` … そのパソコンの Chrome で、コガバスと西鉄バスナビをタブごと切り替えて全画面表示(`kiosk_urls.txt` → `urls.txt` の順にURLを読む)
- 最初の1回だけ `winget install --id Cloudflare.cloudflared` が必要

## ファイル
- `departures.py` : GTFSを読んで次の発車を返す(標準ライブラリのみ)
- `timetable.py`  : 手入力CSV(JR・米多比のバス・土休日の日)を読む
- `build_pages.py` / `docs/` : GitHub Pages 版(時刻表をJSONにして、軽いページで表示する)
- `board.py`      : Streamlit 版の見た目、1画面に収める処理、西鉄バスナビとの切り替え(全画面で共通)
- `config.py`     : 設置場所ごとの設定
- `screens.py` / `app.py` / `site_*.py` : 画面の一覧と入口(`site_*.py` はサーバー用、1か所だけ表示)
- `home.py`       : トップページ(メニュー。手元で起動したときだけ)
- `pages/`        : 4つの設置場所の画面
- `test_departures.py` : 動作テスト(`python test_departures.py`)

"""設置場所ごとの設定。ここを書き換えれば表示が変わります。"""

# コガバス ⇔ 西鉄バス を切り替える間隔(秒)
SWITCH_SECONDS = 6

# 発車時刻・残り時間を計算し直す間隔(秒)。発車したバスはこの間隔で一覧から消える
REFRESH_SECONDS = 15

# お知らせを書く Google スプレッドシートの「ウェブに公開」した CSV の URL。
# 列は「場所 / お知らせ / 表示開始 / 表示終了」。空なら docs/notices.txt だけを使う。
NOTICES_CSV_URL = ("https://docs.google.com/spreadsheets/d/e/2PACX-1vQItsOSTgP1brgABVPuwHZQjiBy3YMOAloMcljw5fCzxisfY6kk"
                   "-g_VTPPZiaW2iY1N16POiwYuyjcn/pub?gid=0&single=true&output=csv")

# 青柳・コスモス館・古賀駅(コガバス + 西鉄バスの切り替え表示)
# stop          : コガバスのバス停名(GTFSの stop_name と同じ文字)
# routes        : 表示するコガバスの路線名
# nishitetsu_url : 西鉄バス「バスナビ」サイネージ用ページのURL。このページを元のまま開いて
#                  コガバスの画面と交互に表示する(西鉄のページには一切手を加えない)
# nnr_template   : 西鉄バスナビと同じデザインで表示する(18 = 横長・2列 / 16 = 縦長・1列)。消すと独自デザイン
# layout         : ディスプレイの向き。"wide" 横長(1980×1280) / "tall" 縦長(1280×1980)
SITES = {
    "aoyagi": {
        "place": "青柳郵便局",
        "layout": "wide",
        "nnr_template": 18,
        "stop": "青柳四ツ角",
        "routes": ["JR古賀線"],
        "nishitetsu_url": "https://navi.nnr.co.jp/jikoku/device/busnavi?viewmode=0&cd=0328",
    },
    "cosmos": {
        "place": "コスモス館",
        "layout": "tall",
        "nnr_template": 16,
        "stop": "コスモス館",
        "routes": ["JR古賀線", "小竹線"],
        "nishitetsu_url": "https://navi.nnr.co.jp/jikoku/device/busnavi?viewmode=0&cd=0322&pos=1",
    },
    "koga_station": {
        "place": "JR古賀駅 自由通路",
        "layout": "tall",
        "nnr_template": 16,
        "stop": "JR古賀駅東口",
        "routes": ["JR古賀線"],
        "nishitetsu_url": "https://navi.nnr.co.jp/jikoku/device/busnavi?viewmode=0&cd=0321&pos=1",
    },
}

# 米多比(西鉄バスで古賀駅へ → JRへの乗り継ぎ案内)
YATABI = {
    "place": "米多比郵便局",
    "layout": "wide",   # 横長(1980×1280)
    "nnr_template": 18, # 西鉄バスナビ風のデザイン(青柳とそろえる)。消すと独自デザイン
    "stop": "米多比",
    # バスが古賀駅に着いてから改札・ホームまでにかかる分数。これより後の電車を案内する
    "transfer_minutes": 3,
    # JRの方面(data/jr_koga.csv の「方面」列と同じ文字)
    "directions": ["博多方面", "小倉方面"],
    # 画面に出す方面の表記(初めての人にも分かる名前にする)
    "direction_labels": {"博多方面": "博多駅 方面", "小倉方面": "小倉駅 方面"},
}

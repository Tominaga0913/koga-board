"""GitHub Pages 用の軽い発車標ページ(docs/)を作る。

    python build_pages.py

時刻表(コガバスのGTFS、米多比の手入力CSV)を「日付ごとの発車一覧」のJSONにして docs/data/ に書き出す。
ページ(docs/*.html)はそのJSONを読み、ブラウザの中で次の発車を計算して表示する。
Streamlit を使わないので、開いてすぐ表示され、サーバーの休止もない。

時刻表や config.py を変えたら、このプログラムを動かしてから GitHub に Push する。
"""
import json
from datetime import date, timedelta
from pathlib import Path

from config import NOTICES_CSV_URL, SITES, SWITCH_SECONDS, YATABI
from departures import is_running, load_feed, stop_ids_by_name
from timetable import find_csv, load_buses, load_holidays, load_trains

ROOT = Path(__file__).parent
DOCS = ROOT / "docs"
DATA = DOCS / "data"
DATA_DIR = ROOT / "data"

# ページのファイル名(URLの最後の部分)
PAGE_NAMES = {"aoyagi": "aoyagi", "cosmos": "cosmos", "koga_station": "koga"}
# お知らせ(docs/notices.txt)で使う場所の名前
AREAS = {"yatabi": "米多比", "aoyagi": "青柳", "cosmos": "コスモス館", "koga": "古賀駅"}

NOTICES_TEMPLATE = """# 発車標の画面の下に出す「お知らせ」です。GitHub のサイトでこのファイルを開き、
# 右上の鉛筆マーク(Edit)で書き換えて「Commit changes」すると、数分で画面に出ます。
#
# 書き方: 1行に1つ。「場所: お知らせの文章」
#   場所は 全部 / 米多比 / 青柳 / コスモス館 / 古賀駅(「青柳、コスモス館」のように複数も可)
#   # で始まる行は説明なので、画面には出ません。お知らせを消すときは、その行を消します。
#
# 例(先頭の # を消すと画面に出ます):
# 全部: 本日は道路工事のため、約10分遅れています
# 青柳: 青柳四ツ角のバス停は、11月30日まで移設しています
"""


def koga_zip():
    zips = sorted(DATA_DIR.glob("*.zip"))
    koga = [z for z in zips if "kogabus" in z.name.lower()]
    return (koga or zips)[0]


def feed_period(feed):
    """時刻表が有効な期間(calendar の最初〜最後の日)。"""
    starts = [c["start"] for c in feed.calendar.values()]
    ends = [c["end"] for c in feed.calendar.values()]
    to_date = lambda s: date(int(s[:4]), int(s[4:6]), int(s[6:]))
    return to_date(min(starts)), to_date(max(ends))


def site_days(feed, site, first, last):
    """日付ごとの発車一覧。{日付: [[秒, 路線番号, 行き先番号], ...]}。

    秒はその日の0時から(25:10 のような24時超えもそのまま)。ブラウザ側で前日分の24時超えも見る。
    """
    ids = stop_ids_by_name(feed, site["stop"])
    routes, heads, days = [], [], {}

    def index(lst, v):
        if v not in lst:
            lst.append(v)
        return lst.index(v)

    d = first
    while d <= last:
        rows = []
        for sid in ids:
            for sec, trip_id in feed.stop_times.get(sid, []):
                trip = feed.trips.get(trip_id)
                if not trip or not is_running(feed, trip["service_id"], d):
                    continue
                route = feed.routes.get(trip["route_id"], "")
                if site["routes"] and route not in site["routes"]:
                    continue
                rows.append([sec, index(routes, route), index(heads, trip["headsign"] or route)])
        if rows:
            days[d.isoformat()] = sorted(rows)
        d += timedelta(days=1)
    return {"routes": routes, "heads": heads, "days": days,
            "first": first.isoformat(), "last": last.isoformat()}


def yatabi_data():
    bus_path, bus_sample = find_csv("yatabi_bus")
    jr_path, jr_sample = find_csv("jr_koga")
    return {
        "buses": [[b["diagram"], b["dep"], b["arr"], b["dest"]] for b in load_buses(bus_path)],
        "trains": [[t["direction"], t["diagram"], t["sec"], t["type"], t["dest"]] for t in load_trains(jr_path)],
        "holidays": sorted(h.isoformat() for h in load_holidays()),
        "sample": bus_sample or jr_sample,
    }


def page_html(name, title, conf):
    """各ページのHTML。中身は board.js が作る。"""
    return f"""<!doctype html>
<html lang="ja" translate="no">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="google" content="notranslate">
<title>{title}</title>
<link rel="stylesheet" href="board.css">
</head>
<body class="notranslate">
<div id="board"></div>
<script>window.BOARD = {json.dumps(conf, ensure_ascii=False)};</script>
<script src="board.js"></script>
</body>
</html>
"""


def main():
    DATA.mkdir(parents=True, exist_ok=True)
    feed = load_feed(koga_zip())
    first, last = feed_period(feed)
    first = max(first, date.today() - timedelta(days=2))   # 過去の日付は要らない

    links = []
    for key, site in SITES.items():
        name = PAGE_NAMES[key]
        (DATA / f"{name}.json").write_text(
            json.dumps(site_days(feed, site, first, last), ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8")
        conf = {"kind": "koga", "data": f"data/{name}.json", "stop": site["stop"], "area": AREAS[name], "noticesCsv": NOTICES_CSV_URL,
                "template": site["nnr_template"], "nnr": site["nishitetsu_url"], "sec": SWITCH_SECONDS}
        title = f'{site["place"]} 発車案内'
        (DOCS / f"{name}.html").write_text(page_html(name, title, conf), encoding="utf-8")
        links.append((name, site["place"]))

    (DATA / "yatabi.json").write_text(
        json.dumps(yatabi_data(), ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    conf = {"kind": "yatabi", "data": "data/yatabi.json", "stop": YATABI["stop"], "area": AREAS["yatabi"], "noticesCsv": NOTICES_CSV_URL,
            "transfer": YATABI["transfer_minutes"], "directions": YATABI["directions"],
            "labels": YATABI.get("direction_labels", {})}
    (DOCS / "yatabi.html").write_text(
        page_html("yatabi", f'{YATABI["place"]} 乗り継ぎ案内', conf), encoding="utf-8")
    links.insert(0, ("yatabi", YATABI["place"]))

    items = "".join(f'<li><a href="{n}.html">{p}</a></li>' for n, p in links)
    (DOCS / "index.html").write_text(f"""<!doctype html>
<html lang="ja" translate="no"><head><meta charset="utf-8"><title>コガバス発車標</title>
<style>body{{font-family:Meiryo,sans-serif;background:#1f9d55;color:#fff;padding:24px}}
a{{color:#fff;font-size:28px}} li{{margin:12px 0}}</style></head>
<body><h1>コガバス発車標</h1><ul>{items}</ul></body></html>
""", encoding="utf-8")
    (DOCS / ".nojekyll").write_text("", encoding="utf-8")   # GitHub Pages にそのまま出してもらう
    notices = DOCS / "notices.txt"
    if not notices.exists():                                 # 書いてあるお知らせは消さない
        notices.write_text(NOTICES_TEMPLATE, encoding="utf-8")
    print(f"docs/ を作りました(コガバスの時刻表: {first} 〜 {last})")


if __name__ == "__main__":
    main()

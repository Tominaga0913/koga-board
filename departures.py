"""GTFS-JP(ZIP)から、指定バス停の「次の発車」を取り出す処理。

標準ライブラリだけで動きます(追加インストール不要)。
"""
import csv
import io
import zipfile
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

JST = ZoneInfo("Asia/Tokyo")


@dataclass
class Feed:
    stops: dict            # stop_id -> stop_name
    routes: dict           # route_id -> route_name
    trips: dict            # trip_id -> {route_id, service_id, headsign}
    stop_times: dict       # stop_id -> [(秒, trip_id), ...] 秒の昇順
    calendar: dict         # service_id -> {曜日: bool, start, end}
    calendar_dates: dict   # (service_id, YYYYMMDD) -> 1(追加) or 2(運休)
    trip_stops: dict = None  # trip_id -> [stop_id, ...] 停車順(経由するバス停の表示に使う)


def _read_csv(zf, name):
    """ZIP内のCSVを辞書のリストで返す。無ければ空リスト。"""
    if name not in zf.namelist():
        return []
    with zf.open(name) as f:
        text = io.TextIOWrapper(f, encoding="utf-8-sig", newline="")
        return list(csv.DictReader(text))


def parse_time(s):
    """'25:10:00' のような24時超えの時刻も秒に変換する。'7:05' のように秒なしでもよい。"""
    s = (s or "").strip()
    if not s:
        return None
    h, m, sec = ([int(x) for x in s.split(":")] + [0])[:3]
    return h * 3600 + m * 60 + sec


def load_feed(zip_path):
    with zipfile.ZipFile(zip_path) as zf:
        stops = {r["stop_id"]: r["stop_name"] for r in _read_csv(zf, "stops.txt")}
        routes = {}
        for r in _read_csv(zf, "routes.txt"):
            routes[r["route_id"]] = r.get("route_long_name") or r.get("route_short_name") or ""
        trips = {
            r["trip_id"]: {
                "route_id": r["route_id"],
                "service_id": r["service_id"],
                "headsign": r.get("trip_headsign", ""),
            }
            for r in _read_csv(zf, "trips.txt")
        }
        rows = _read_csv(zf, "stop_times.txt")
        # 各便の終点(最後の停車)は「到着」なので発車一覧に出さない
        last_seq = {}
        for r in rows:
            seq = int(r.get("stop_sequence") or 0)
            last_seq[r["trip_id"]] = max(seq, last_seq.get(r["trip_id"], seq))
        order = {}
        for r in rows:
            order.setdefault(r["trip_id"], []).append((int(r.get("stop_sequence") or 0), r["stop_id"]))
        trip_stops = {t: [s for _, s in sorted(lst)] for t, lst in order.items()}
        stop_times = {}
        for r in rows:
            sec = parse_time(r.get("departure_time")) or parse_time(r.get("arrival_time"))
            if sec is None:
                continue
            if "stop_sequence" in r and int(r["stop_sequence"] or 0) == last_seq[r["trip_id"]]:
                continue
            stop_times.setdefault(r["stop_id"], []).append((sec, r["trip_id"]))
        for lst in stop_times.values():
            lst.sort()
        calendar = {}
        for r in _read_csv(zf, "calendar.txt"):
            calendar[r["service_id"]] = {
                "days": [r[d] == "1" for d in (
                    "monday", "tuesday", "wednesday", "thursday",
                    "friday", "saturday", "sunday")],
                "start": r["start_date"],
                "end": r["end_date"],
            }
        calendar_dates = {
            (r["service_id"], r["date"]): int(r["exception_type"])
            for r in _read_csv(zf, "calendar_dates.txt")
        }
    return Feed(stops, routes, trips, stop_times, calendar, calendar_dates, trip_stops)


def is_running(feed, service_id, d: date):
    """service_id が日付 d に運行するか(通常ダイヤ + 例外日)。"""
    key = (service_id, d.strftime("%Y%m%d"))
    exc = feed.calendar_dates.get(key)
    if exc == 1:
        return True
    if exc == 2:
        return False
    cal = feed.calendar.get(service_id)
    if not cal:
        return False
    ymd = d.strftime("%Y%m%d")
    return cal["start"] <= ymd <= cal["end"] and cal["days"][d.weekday()]


def stop_ids_by_name(feed, name):
    """同じ名前のバス停(乗り場違い)をまとめて取得。"""
    return [sid for sid, n in feed.stops.items() if n == name]


def stop_names(feed):
    """発車のあるバス停名を重複なしで返す。"""
    return sorted({feed.stops[s] for s in feed.stop_times if s in feed.stops})


def next_departures(feed, stop_name, now=None, limit=3, routes=None):
    """stop_name の、now 以降の発車を limit 件返す。

    routes に路線名のリストを渡すと、その路線だけに絞る(例: ["JR古賀線"])。
    戻り値: [{"time": "14:45", "route": 路線名, "headsign": 行き先, "minutes": あと何分}, ...]
    """
    now = now or datetime.now(JST)
    today = now.date()
    now_sec = now.hour * 3600 + now.minute * 60 + now.second
    ids = stop_ids_by_name(feed, stop_name)

    found = []
    # 今日のダイヤ と、深夜をまたぐ前日のダイヤ(25:10 など)の両方を見る
    for offset, base in ((0, now_sec), (-1, now_sec + 86400)):
        d = today + timedelta(days=offset)
        for sid in ids:
            for sec, trip_id in feed.stop_times.get(sid, []):
                if sec < base:
                    continue
                trip = feed.trips.get(trip_id)
                if not trip or not is_running(feed, trip["service_id"], d):
                    continue
                if routes and feed.routes.get(trip["route_id"]) not in routes:
                    continue
                # 実際の発車時刻(今日0時からの秒)
                actual = sec - (86400 if offset == -1 else 0)
                found.append((actual, trip))
    found.sort(key=lambda x: x[0])

    result = []
    for actual, trip in found[:limit]:
        h, m = divmod(actual // 60, 60)
        result.append({
            "time": f"{h % 24:02d}:{m:02d}",
            "route": feed.routes.get(trip["route_id"], ""),
            "headsign": trip["headsign"],
            "minutes": max(0, (actual - now_sec) // 60),
        })
    return result

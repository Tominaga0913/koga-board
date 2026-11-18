"""手入力のCSV時刻表(JR古賀駅・米多比のバス)を読む処理。

標準ライブラリだけで動きます。

data/jr_koga.csv     … 方面,ダイヤ,時刻,種別,行き先
data/yatabi_bus.csv  … ダイヤ,米多比発,古賀駅着,行き先

本物のファイルが無いときは *.sample.csv(サンプル)を読みます。
ダイヤは「平日」か「土休日」。土日と、data/holidays.csv に書いた日(祝日・年末年始など)が土休日です。
"""
import csv
from datetime import date
from pathlib import Path

from departures import parse_time

DATA_DIR = Path(__file__).parent / "data"


def find_csv(name):
    """(パス, サンプルかどうか) を返す。どちらも無ければ (None, False)。"""
    real = DATA_DIR / f"{name}.csv"
    if real.exists():
        return real, False
    sample = DATA_DIR / f"{name}.sample.csv"
    if sample.exists():
        return sample, True
    return None, False


def read_rows(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        return [r for r in csv.DictReader(f) if any((v or "").strip() for v in r.values())]


def load_holidays(path=DATA_DIR / "holidays.csv"):
    """土休日ダイヤで走る日(土日以外)。1行に1日、YYYY-MM-DD で書く。# で始まる行は説明。"""
    days = set()
    if not path.exists():
        return days
    with open(path, encoding="utf-8-sig") as f:
        for line in f:
            s = line.split("#", 1)[0].strip().split(",")[0].strip()
            if not s:
                continue
            try:
                days.add(date.fromisoformat(s))
            except ValueError:
                continue
    return days


def diagram_of(d, holidays=None):
    """その日のダイヤ。土日と holidays(省略時は data/holidays.csv)の日は土休日。"""
    if holidays is None:
        holidays = load_holidays()
    return "土休日" if d.weekday() >= 5 or d in holidays else "平日"


def fmt(sec):
    h, m = divmod(sec // 60, 60)
    return f"{h % 24:02d}:{m:02d}"


def now_sec(now):
    return now.hour * 3600 + now.minute * 60 + now.second


def load_trains(path):
    """[{direction, diagram, sec, type, dest}, ...] 時刻順。"""
    trains = []
    for r in read_rows(path):
        sec = parse_time(r["時刻"])
        if sec is None:
            continue
        trains.append({
            "direction": r["方面"].strip(),
            "diagram": r["ダイヤ"].strip(),
            "sec": sec,
            "type": r.get("種別", "").strip(),
            "dest": r.get("行き先", "").strip(),
        })
    trains.sort(key=lambda t: t["sec"])
    return trains


def next_trains(trains, direction, diagram, after_sec, limit=1):
    """after_sec 以降に発車する direction 方面の列車を limit 本返す。"""
    out = [t for t in trains
           if t["direction"] == direction and t["diagram"] == diagram and t["sec"] >= after_sec]
    return out[:limit]


def load_buses(path):
    """[{diagram, dep, arr, dest}, ...] 発車順。"""
    buses = []
    for r in read_rows(path):
        dep, arr = parse_time(r["米多比発"]), parse_time(r["古賀駅着"])
        if dep is None or arr is None:
            continue
        buses.append({
            "diagram": r["ダイヤ"].strip(),
            "dep": dep,
            "arr": arr,
            "dest": r.get("行き先", "").strip(),
        })
    buses.sort(key=lambda b: b["dep"])
    return buses


def next_buses(buses, diagram, after_sec, limit=3):
    return [b for b in buses if b["diagram"] == diagram and b["dep"] >= after_sec][:limit]

"""次発抽出の動作テスト。 python test_departures.py"""
import tempfile
import zipfile
from datetime import datetime
from pathlib import Path

from departures import JST, load_feed, next_departures, parse_time, stop_names

FILES = {
    "stops.txt": "stop_id,stop_name\n1,コスモス館\n2,JR古賀駅\n",
    "routes.txt": "route_id,route_long_name\nR1,小竹線\n",
    "trips.txt": (
        "route_id,service_id,trip_id,trip_headsign\n"
        "R1,WD,T1,JR古賀駅\nR1,WD,T2,JR古賀駅\nR1,WD,T3,JR古賀駅\n"
        "R1,WD,T4,JR古賀駅\nR1,HOL,T5,臨時便\n"
    ),
    "stop_times.txt": (
        "trip_id,stop_id,departure_time,arrival_time\n"
        "T1,1,08:00:00,08:00:00\nT2,1,09:30:00,09:30:00\n"
        "T3,1,17:10:00,17:10:00\nT4,1,25:10:00,25:10:00\n"
        "T5,1,10:00:00,10:00:00\n"
    ),
    "calendar.txt": (
        "service_id,monday,tuesday,wednesday,thursday,friday,saturday,sunday,start_date,end_date\n"
        "WD,1,1,1,1,1,0,0,20260401,20270331\n"
        "HOL,0,0,0,0,0,0,0,20260401,20270331\n"
    ),
    # 2026-10-14(水)に臨時便HOLを追加
    "calendar_dates.txt": "service_id,date,exception_type\nHOL,20261014,1\n",
}


def make_zip(path):
    with zipfile.ZipFile(path, "w") as zf:
        for name, text in FILES.items():
            zf.writestr(name, "﻿" + text)  # BOM付きでも読めるか


def main():
    with tempfile.TemporaryDirectory() as d:
        zp = Path(d) / "sample.zip"
        make_zip(zp)
        feed = load_feed(zp)
        assert stop_names(feed) == ["コスモス館"], stop_names(feed)

        # 水曜9:00 -> 09:30, 10:00(臨時), 17:10
        r = next_departures(feed, "コスモス館", datetime(2026, 10, 14, 9, 0, tzinfo=JST), 3)
        assert [x["time"] for x in r] == ["09:30", "10:00", "17:10"], r
        assert r[0]["minutes"] == 30

        # 水曜18:00 -> 水曜ダイヤの 25:10 (= 木曜1:10) が「あと430分」で出る
        r = next_departures(feed, "コスモス館", datetime(2026, 10, 14, 18, 0, tzinfo=JST), 3)
        assert [x["time"] for x in r] == ["01:10"], r
        assert r[0]["minutes"] == 430, r

        # 木曜0:30 -> 前日(水)ダイヤの25:10 = 1:10 が出る
        r = next_departures(feed, "コスモス館", datetime(2026, 10, 15, 0, 30, tzinfo=JST), 3)
        assert [x["time"] for x in r] == ["01:10", "08:00", "09:30"], r
        assert r[0]["minutes"] == 40, r

        # 日曜は平日ダイヤが走らない
        r = next_departures(feed, "コスモス館", datetime(2026, 10, 18, 7, 0, tzinfo=JST), 3)
        assert r == [], r

        # 路線で絞り込み
        r = next_departures(feed, "コスモス館", datetime(2026, 10, 14, 9, 0, tzinfo=JST), 3,
                            routes=["JR古賀線"])
        assert r == [], r

        # 終点(最後の停車)は発車一覧に出さない: T1 は 1 → 2 で、2 が終点
        files = dict(FILES)
        files["stop_times.txt"] = (
            "trip_id,stop_id,departure_time,arrival_time,stop_sequence\n"
            "T1,1,08:00:00,08:00:00,1\nT1,2,08:20:00,08:20:00,2\n"
        )
        zp2 = Path(d) / "terminal.zip"
        with zipfile.ZipFile(zp2, "w") as zf:
            for name, text in files.items():
                zf.writestr(name, text)
        feed2 = load_feed(zp2)
        assert stop_names(feed2) == ["コスモス館"], stop_names(feed2)

    # 秒なしの時刻(手入力CSV用)
    assert parse_time("7:05") == 7 * 3600 + 5 * 60
    assert parse_time("25:10:30") == 25 * 3600 + 10 * 60 + 30

    test_timetable()
    test_build_pages()
    print("OK: すべてのテストに成功")


def test_build_pages():
    """GitHub Pages 用に書き出す「日付ごとの発車一覧」が、正しい日・時刻・行き先になっているか。"""
    from datetime import date
    from build_pages import site_days

    with tempfile.TemporaryDirectory() as d:
        zp = Path(d) / "sample.zip"
        make_zip(zp)
        feed = load_feed(zp)
        site = {"stop": "コスモス館", "routes": ["小竹線"]}
        out = site_days(feed, site, date(2026, 10, 14), date(2026, 10, 18))
        days = out["days"]
        # 水曜(臨時便あり): 8:00, 9:30, 10:00(臨時), 17:10, 25:10(翌1:10)
        assert [r[0] for r in days["2026-10-14"]] == [8 * 3600, 9.5 * 3600, 10 * 3600,
                                                     17 * 3600 + 600, 25 * 3600 + 600], days["2026-10-14"]
        assert out["heads"][days["2026-10-14"][2][2]] == "臨時便"
        assert "2026-10-18" not in days            # 日曜は平日ダイヤが走らない
        # 路線が違えば何も出ない
        assert site_days(feed, {"stop": "コスモス館", "routes": ["JR古賀線"]},
                         date(2026, 10, 14), date(2026, 10, 14))["days"] == {}


def test_timetable():
    """米多比の乗り継ぎ(手入力CSV)のテスト。"""
    import timetable as tt
    from datetime import date

    # 土休日の判定: 土日に加えて holidays.csv の日
    hol = {date(2026, 11, 23)}
    assert tt.diagram_of(date(2026, 11, 23), hol) == "土休日"   # 月曜だが祝日
    assert tt.diagram_of(date(2026, 11, 24), hol) == "平日"
    assert tt.diagram_of(date(2026, 11, 22), hol) == "土休日"   # 日曜

    with tempfile.TemporaryDirectory() as d:
        hp = Path(d) / "holidays.csv"
        hp.write_text("# 説明\n2026-01-01  # 元日\n\nxx\n2026-05-06\n", encoding="utf-8")
        assert tt.load_holidays(hp) == {date(2026, 1, 1), date(2026, 5, 6)}

        jr = Path(d) / "jr.csv"
        jr.write_text("方面,ダイヤ,時刻,種別,行き先\n"
                      "博多方面,平日,14:35,普通,博多\n博多方面,平日,14:48,快速,博多\n"
                      "小倉方面,平日,14:39,普通,小倉\n博多方面,土休日,14:40,普通,博多\n",
                      encoding="utf-8")
        trains = tt.load_trains(jr)
        bus_arr = tt.parse_time("14:32")
        # 到着14:32 + 乗り換え3分 = 14:35 以降 → 14:35 の普通が最初
        r = tt.next_trains(trains, "博多方面", "平日", bus_arr + 3 * 60)
        assert [t["sec"] for t in r] == [tt.parse_time("14:35")], r
        # 乗り換え5分なら 14:35 には間に合わず 14:48 の快速
        r = tt.next_trains(trains, "博多方面", "平日", bus_arr + 5 * 60)
        assert r[0]["type"] == "快速" and r[0]["sec"] == tt.parse_time("14:48"), r
        # 土休日ダイヤ・方面の絞り込み
        assert [t["sec"] for t in tt.next_trains(trains, "博多方面", "土休日", 0)] == [tt.parse_time("14:40")]
        assert tt.next_trains(trains, "小倉方面", "土休日", 0) == []

        bus = Path(d) / "bus.csv"
        bus.write_text("ダイヤ,米多比発,古賀駅着,行き先\n平日,14:10,14:32,JR古賀駅\n平日,13:10,13:32,JR古賀駅\n",
                       encoding="utf-8")
        buses = tt.load_buses(bus)
        assert [b["dep"] for b in buses] == [tt.parse_time("13:10"), tt.parse_time("14:10")]  # 発車順
        r = tt.next_buses(buses, "平日", tt.parse_time("13:30"))
        assert len(r) == 1 and r[0]["arr"] == tt.parse_time("14:32"), r


if __name__ == "__main__":
    main()

"""米多比郵便局: 西鉄バスの古賀駅到着時刻と、乗り継げるJRの電車の案内"""
from datetime import datetime
from html import escape

import streamlit as st

from board import (NNR_CSS, duration_html, fit_to_screen, foot_html, head_html, nnr_left,
                   order_label, orientation, row_count, setup)
from config import REFRESH_SECONDS, YATABI
from departures import JST
from timetable import (diagram_of, find_csv, fmt, load_buses, load_trains,
                       next_buses, next_trains, now_sec)

setup(f'{YATABI["place"]} 乗り継ぎ案内', YATABI.get("layout", "wide"))

bus_path, bus_sample = find_csv("yatabi_bus")
jr_path, jr_sample = find_csv("jr_koga")
if bus_path is None or jr_path is None:
    st.error("data/yatabi_bus.csv と data/jr_koga.csv を用意してください(README参照)")
    st.stop()

rows = row_count()
transfer = YATABI["transfer_minutes"] * 60


def train_html(direction, bus_arr, trains, diagram):
    found = next_trains(trains, direction, diagram, bus_arr + transfer, limit=1)
    if not found:
        return '<div class="x-train"><div class="none">接続する電車はありません</div></div>'
    t = found[0]
    if "特急" in t["type"] or "急行" in t["type"]:
        cls = " express"
    elif "快速" in t["type"]:
        cls = " rapid"
    else:
        cls = ""
    kind = f'<span class="kind{cls}">{escape(t["type"])}</span>' if t["type"] else ""
    wait = (t["sec"] - bus_arr) // 60
    return (
        f'<div class="x-train"><div class="line">{kind}<span class="t num">{fmt(t["sec"])}</span></div>'
        f'<div class="w"><span class="to">{escape(t["dest"])}行</span>到着後 <b class="num">{wait}</b>分</div></div>'
    )


# ---------- 西鉄バスナビ風のデザイン(青柳などと見た目をそろえる) ----------
YATABI_NNR_CSS = """
<style>
.nnr.t18 .list th { height: 64px; font-size: 40px; }   /* 列の見出しを大きく */
.nnr.t18 .list th { width: 25%; }   /* 4つの列をすべて同じ幅に */
.nnr .op { display: inline-block; font-size: 30px; line-height: 1em; padding: 4px 8px; margin-right: 14px;
  vertical-align: middle; border: 3px solid #fff; color: #fff; }
.nnr .op.rapid { background: #e60012; border-color: #e60012; color: #fff; }   /* 快速は赤 */
.nnr .op.express { background: #fff; color: var(--frame); }
.nnr .jkn { vertical-align: middle; }

/* いちばん早く来るバスの行を大きく、2本目以降は小さく */
.nnr.t18 tr.first .gyo { height: 300px; }
.nnr.t18 tr.first .jkn { font-size: 100px; }
.nnr.t18 tr.first .now, .nnr.t18 tr.first .now.long { font-size: 48px; }
.nnr.t18 tr.first .kiy { font-size: 40px; }
.nnr.t18 tr.first .op { font-size: 42px; padding: 6px 12px; }
.nnr.t18 tr.next .gyo { height: 175px; }
.nnr.t18 tr.next .jkn { font-size: 52px; }
.nnr.t18 tr.next .now, .nnr.t18 tr.next .now.long { font-size: 28px; }
.nnr.t18 tr.next .kiy { font-size: 26px; }
.nnr.t18 tr.next .op { font-size: 24px; padding: 3px 6px; }
.nnr .msg { width: 100%; border: 0; margin-top: 6px; }
.nnr .msg th, .nnr .msg td { border: 2px solid #fff; color: #000; font-size: 42px; line-height: 1em;
  height: 62px; vertical-align: middle; }
.nnr .msg th { width: 200px; background: #FFFF99; text-align: right; padding-right: 8px; }
.nnr .msg td { background: #FFFF33; padding-left: 12px; text-align: left; }
</style>
"""


def nnr_train_td(direction, bus_arr, trains, diagram):
    found = next_trains(trains, direction, diagram, bus_arr + transfer, limit=1)
    if not found:
        return '<td class="gyo txtct"><span class="now">接続する電車はありません</span></td>'
    t = found[0]
    if "特急" in t["type"] or "急行" in t["type"]:
        cls = " express"
    elif "快速" in t["type"]:
        cls = " rapid"
    else:
        cls = ""
    kind = f'<span class="op{cls}">{escape(t["type"])}</span>' if t["type"] else ""
    wait = (t["sec"] - bus_arr) // 60
    return (
        f'<td class="gyo txtct">{kind}<span class="jkn">{fmt(t["sec"])}</span><br/>'
        f'<span class="now">{escape(t["dest"])}行 到着後{wait}分</span></td>'
    )


def yatabi_nnr_html(now, buses, trains, diagram, count=3):
    labels = YATABI.get("direction_labels", {})
    dirs = YATABI["directions"]
    head = (
        '<tr><th class="header_title">'
        f'<div class="text_title"><span class="brand">乗り継ぎ案内</span>{escape(YATABI["stop"])} → JR古賀駅</div>'
        f'<div class="text_time">{now:%H:%M} 現在の状況</div></th></tr>'
    )
    rows = []
    for i, b in enumerate(buses[:count]):
        mins = max(0, (b["dep"] - now_sec(now)) // 60)
        rows.append(
            f'<tr class="{"first" if i == 0 else "next"}">'
            f'<td class="gyo txtct"><span class="jkn">{fmt(b["dep"])}</span><br/>'
            f'<span class="now{" long" if mins >= 60 else ""}">{nnr_left(mins)}</span></td>'
            f'<td class="gyo txtct"><span class="jkn">{fmt(b["arr"])}</span><br/>'
            f'<span class="kiy">{escape(b["dest"] or "JR古賀駅")}着</span></td>'
            + "".join(nnr_train_td(d, b["arr"], trains, diagram) for d in dirs)
            + "</tr>"
        )
    if not buses:
        rows.append(f'<tr><td class="gyo txtct" colspan="{2 + len(dirs)}">'
                    '<span class="yki">本日のバスは終了しました</span></td></tr>')
    while len(rows) < count:
        rows.append('<tr class="next pad">' + '<td class="gyo"></td>' * (2 + len(dirs)) + "</tr>")
    table = (
        '<table class="list"><tr>'
        '<th class="y-dep">米多比発 発車まで</th><th class="y-arr">古賀駅着</th>'
        + "".join(f"<th>JR {escape(labels.get(d, d))}</th>" for d in dirs)
        + "</tr>" + "".join(rows) + "</table>"
    )
    notice = ""
    if bus_sample or jr_sample:
        notice = ('<table class="msg"><tr><th>お知らせ</th>'
                  "<td>サンプルデータを表示中です(実際の時刻ではありません)</td></tr></table>")
    return (
        '<div class="nnr t18 notranslate" translate="no" data-w="1920">'
        f'<table class="disp">{head}<tr><td class="va_top">{table}{notice}</td></tr></table></div>'
    )


@st.fragment(run_every=REFRESH_SECONDS)
def yatabi_nnr():
    now = datetime.now(JST)
    diagram = diagram_of(now.date())
    buses = next_buses(load_buses(bus_path), diagram, now_sec(now), limit=3)
    st.markdown(yatabi_nnr_html(now, buses, load_trains(jr_path), diagram), unsafe_allow_html=True)


@st.fragment(run_every=REFRESH_SECONDS)
def yatabi():
    now = datetime.now(JST)
    diagram = diagram_of(now.date())
    buses = next_buses(load_buses(bus_path), diagram, now_sec(now), limit=rows)
    trains = load_trains(jr_path)
    dirs = YATABI["directions"]

    html = [f'<div class="board notranslate {orientation()}" translate="no">']
    if bus_sample or jr_sample:
        html.append('<div class="sample">サンプルデータを表示中です(実際の時刻ではありません)</div>')
    html.append(head_html(f'{YATABI["place"]} ・ 西鉄バス → JR古賀駅 乗り継ぎ案内',
                          YATABI["stop"], now, suffix="バス停"))

    if not buses:
        html.append('<div class="b-empty">本日のバスは終了しました'
                    "<small>またのご利用をお待ちしております</small></div>")
    else:
        html.append(
            '<div class="x-cols"><span></span><span>バス発車</span><span>古賀駅 到着</span>'
            + "".join(
                f'<span class="dir"><small>JR</small>{escape(YATABI.get("direction_labels", {}).get(d, d))}</span>'
                for d in dirs)
            + "</div>"
        )
        for i, b in enumerate(buses):
            mins = (b["dep"] - now_sec(now)) // 60
            if mins <= 0:
                left = '<div class="m soon">まもなく発車</div>'
            else:
                hurry = " soon" if mins <= 2 else ""      # 残り1〜2分は色を変える
                left = f'<div class="m{hurry}">あと {duration_html(mins)}</div>'
            html.append(
                f'<div class="x-row{" first" if i == 0 else ""}">'
                f'<span class="order">{order_label(i)}</span>'
                f'<div class="x-dep"><div class="t num">{fmt(b["dep"])}</div>{left}</div>'
                f'<div class="x-arr"><div class="t num">{fmt(b["arr"])}</div>'
                f'<div class="s">{escape(b["dest"] or "JR古賀駅")} 着</div></div>'
                + "".join(train_html(d, b["arr"], trains, diagram) for d in dirs)
                + "</div>"
            )

    html.append(foot_html(
        now, f"※ 時刻表に基づく予定時刻です。乗り換えに{YATABI['transfer_minutes']}分以上かかる前提で案内しています。"))
    html.append("</div>")
    st.markdown("".join(html), unsafe_allow_html=True)


if YATABI.get("nnr_template"):
    st.markdown(NNR_CSS + YATABI_NNR_CSS, unsafe_allow_html=True)
    fit_to_screen()
    yatabi_nnr()
else:
    yatabi()

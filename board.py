"""発車標の見た目(全画面で共通)。

各ページはここの関数を呼ぶだけで、同じデザインの発車標になります。
URLの末尾に ?layout=tall を付けると縦長ディスプレイ用の表示になります。
"""
import json
from datetime import datetime
from html import escape
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from config import REFRESH_SECONDS, SWITCH_SECONDS
from departures import JST, load_feed, next_departures, parse_time

DATA_DIR = Path(__file__).parent / "data"
WEEKDAYS = "月火水木金土日"

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@500;700&family=Noto+Sans+JP:wght@400;700;900&display=swap');

:root {
  --bg: #050b18;
  --panel: #0b1630;
  --line: rgba(120, 160, 255, .14);
  --text: #f2f5ff;
  --muted: #8b9bc4;
  --amber: #ffc83d;
  --cyan: #5fd8ff;
  --alert: #ff7a45;
  --koga: #f39800;
  --nishi: #e60033;
}

/* Streamlit の余白・ヘッダーを消してサイネージ向けに */
.stApp { background: radial-gradient(1200px 600px at 20% -10%, #12234d 0%, var(--bg) 60%); }
header[data-testid="stHeader"] { background: transparent; }
[data-testid="stMainBlockContainer"], .block-container {
  padding: 1.5rem 2rem !important; max-width: none !important;
}
footer, #MainMenu { visibility: hidden; }

.board {
  font-family: 'Noto Sans JP', sans-serif;
  color: var(--text);
  background: linear-gradient(180deg, var(--panel) 0%, #081022 100%);
  border: 1px solid var(--line);
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 30px 80px rgba(0, 0, 0, .55), inset 0 1px 0 rgba(255, 255, 255, .05);
  container-type: inline-size;
}
.num { font-family: 'Barlow Condensed', 'Noto Sans JP', sans-serif; font-variant-numeric: tabular-nums; }

/* ヘッダー */
.b-head {
  display: flex; align-items: center; justify-content: space-between; gap: 24px;
  padding: 24px 36px;
  background: linear-gradient(90deg, #1b3fa8 0%, #142f80 55%, #0f2259 100%);
  border-bottom: 3px solid var(--amber);
}
.board.nishi .b-head { background: linear-gradient(90deg, #a8001f 0%, #7d0019 55%, #4f0010 100%); }
.board.koga .b-head { border-bottom-color: var(--koga); }
.b-brand { display: flex; align-items: center; gap: 20px; min-width: 0; }
.b-logo {
  flex: none; display: grid; place-items: center;
  width: 64px; height: 64px; border-radius: 16px;
  background: var(--amber); color: #0b1630; font-size: 34px;
}
.b-label { font-size: 15px; letter-spacing: .3em; color: #c9d6ff; font-weight: 700; }
.b-stop {
  font-size: 44px; font-weight: 900; line-height: 1.15;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.b-stop small { font-size: 22px; font-weight: 700; color: #c9d6ff; margin-left: 10px; }
.b-clock { text-align: right; flex: none; }
.b-time { font-size: 72px; font-weight: 700; line-height: 1; letter-spacing: .02em; }
.b-time .colon { animation: blink 1s steps(1) infinite; }
.b-date { font-size: 18px; color: #c9d6ff; margin-top: 4px; }

/* コガバス / 西鉄バス の切り替えタブ */
.tabs { display: inline-flex; gap: 6px; margin-top: 8px; }
.tab {
  font-size: 15px; font-weight: 700; padding: 3px 14px; border-radius: 999px;
  color: #c9d6ff; border: 1.5px solid rgba(201, 214, 255, .35);
}
.tab.on.koga { background: var(--koga); border-color: var(--koga); color: #1a1000; }
.tab.on.nishi { background: #fff; border-color: #fff; color: var(--nishi); }

/* 一覧 */
.b-cols, .b-row {
  display: grid; grid-template-columns: 110px var(--dep-w, 250px) minmax(0, 1fr) auto;
  align-items: center; gap: 0 24px; padding: 0 36px;
}
.b-cols {
  font-size: 15px; letter-spacing: .2em; color: var(--muted); font-weight: 700;
  padding-top: 14px; padding-bottom: 14px; border-bottom: 1px solid var(--line);
}
.b-cols .r { text-align: right; }
.b-row { min-height: 108px; border-bottom: 1px solid var(--line); }
.b-row:nth-child(even) { background: rgba(255, 255, 255, .018); }
.b-row.first { background: linear-gradient(90deg, rgba(255, 200, 61, .12), rgba(255, 200, 61, 0) 70%); }
.b-row.first .order { background: var(--amber); color: #0b1630; border-color: var(--amber); }

.order {
  justify-self: start;
  font-size: 18px; font-weight: 700; padding: 6px 14px; border-radius: 999px;
  border: 1.5px solid var(--muted); color: var(--muted);
}
.dep { font-size: 64px; font-weight: 700; color: var(--amber); line-height: 1; }
.dest { min-width: 0; }
.dest .to { font-size: 40px; font-weight: 900; line-height: 1.2;
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
.dest .to small { font-size: 22px; font-weight: 700; color: var(--muted); margin-left: 6px; }
.dest .route {
  display: inline-block; margin-top: 6px; font-size: 16px; font-weight: 700;
  padding: 2px 12px; border-radius: 6px; background: rgba(47, 107, 255, .22); color: #b9ccff;
}
.dest .route.r-JR古賀線 { background: rgba(243, 152, 0, .2); color: #ffc670; }
.dest .route.r-小竹線 { background: rgba(0, 166, 81, .22); color: #8be3b0; }
.left { text-align: right; color: var(--cyan); white-space: nowrap; }
.left .n { font-size: 64px; font-weight: 700; line-height: 1; }
.left .u { font-size: 24px; font-weight: 700; margin: 0 4px 0 6px; }
.left .u:last-child { margin-right: 0; }
.left .pre { font-size: 20px; font-weight: 700; margin-right: 8px; color: var(--muted); }
.left.soon { color: var(--alert); font-size: 40px; font-weight: 900; animation: pulse 1.2s ease-in-out infinite; }

.b-empty { padding: 72px 36px; text-align: center; font-size: 36px; font-weight: 700; color: var(--muted); }
.b-empty small { display: block; font-size: 18px; margin-top: 12px; font-weight: 400; }

.b-foot {
  display: flex; justify-content: space-between; gap: 16px;
  padding: 14px 36px; font-size: 14px; color: var(--muted);
}
.sample {
  background: #ff3b30; color: #fff; font-weight: 900; text-align: center;
  padding: 8px; font-size: 18px; letter-spacing: .1em;
}

/* 米多比: 乗り継ぎ案内 */
.x-cols, .x-row {
  display: grid; grid-template-columns: 110px minmax(0, 1.1fr) minmax(0, 1fr) minmax(0, 1fr) minmax(0, 1fr);
  align-items: center; gap: 0 20px; padding: 0 36px;
}
.x-cols {
  font-size: 15px; letter-spacing: .15em; color: var(--muted); font-weight: 700;
  padding-top: 14px; padding-bottom: 14px; border-bottom: 1px solid var(--line);
}
.x-row { min-height: 128px; border-bottom: 1px solid var(--line); }
.x-row:nth-child(even) { background: rgba(255, 255, 255, .018); }
.x-row.first { background: linear-gradient(90deg, rgba(255, 200, 61, .12), rgba(255, 200, 61, 0) 70%); }
.x-row.first .order { background: var(--amber); color: #0b1630; border-color: var(--amber); }
.x-dep .t { font-size: 60px; font-weight: 700; color: var(--amber); line-height: 1; }
.x-dep .m { font-size: 22px; font-weight: 700; color: var(--cyan); margin-top: 4px; }
.x-dep .m .n { font-family: 'Barlow Condensed', sans-serif; font-size: 28px; }
.x-dep .m .u { margin: 0 2px; }
.x-dep .m.soon { color: var(--alert); animation: pulse 1.2s ease-in-out infinite; }
.x-arr .t { font-size: 48px; font-weight: 700; line-height: 1; }
.x-arr .s { font-size: 15px; color: var(--muted); margin-top: 4px; }
.x-train { border-left: 1px solid var(--line); padding-left: 20px; }
.x-train .t { font-size: 44px; font-weight: 700; line-height: 1; }
.x-train .line { display: flex; align-items: center; gap: 10px; }
.x-train .kind {
  flex: none; font-family: 'Noto Sans JP', sans-serif;
  font-size: 20px; font-weight: 900; line-height: 1; letter-spacing: .05em;
  padding: 6px 10px; border-radius: 6px;
  background: #e8ecf7; color: #0b1630;              /* 普通 */
}
.x-train .kind.rapid { background: #ff3b30; color: #fff; }      /* 快速 */
.x-train .kind.express { background: #b05cff; color: #fff; }    /* 特急など */
.x-train .w { font-size: 18px; font-weight: 700; color: var(--cyan); margin-top: 6px; }
.x-train .w b { font-size: 26px; }
.x-train .none { font-size: 18px; color: var(--muted); }

/* 縦長ディスプレイ: 行を高く、文字を大きく */
.board.tall { --dep-w: 310px; }
.dep { white-space: nowrap; }
.board.tall .b-row { min-height: 150px; }
.board.tall .dep, .board.tall .left .n { font-size: 84px; }
.board.tall .dest .to { font-size: 52px; }
.board.tall .b-stop { font-size: 56px; }
.board.tall .b-time { font-size: 92px; }
.board.tall .x-row { min-height: 170px; }

/* 先発を大きく目立たせ、次発以降は小さく */
.b-row.first, .x-row.first { min-height: 160px; box-shadow: inset 8px 0 0 var(--amber); }
.board.nishi .b-row.first { box-shadow: inset 8px 0 0 var(--nishi); }
.b-row.first .order, .x-row.first .order { font-size: 24px; padding: 8px 18px; }
.b-row.first .dep, .b-row.first .left .n { font-size: 96px; }
.b-row.first .dest .to { font-size: 58px; }
.b-row.first .dest .to.long { font-size: 42px; }        /* 長い行き先は1行に収まるよう小さめに */
.board.tall .b-row.first .dest .to.long { font-size: 54px; }
.b-row.first .dest .to small { font-size: 26px; }
.b-row.first .dest .route { font-size: 18px; }
.b-row.first .left .u { font-size: 32px; }
.b-row.first .left .pre { font-size: 26px; }
.b-row.first .left.soon { font-size: 56px; }
.b-row.first .keito { font-size: 40px; min-width: 80px; padding: 10px 14px; }
.board.nishi .b-row.first .dest .via { font-size: 20px; }
.board.nishi .b-row.first .where { font-size: 22px; }

.b-row:not(.first), .x-row:not(.first) { min-height: 84px; }
.b-row:not(.first) .order, .x-row:not(.first) .order { font-size: 15px; padding: 4px 12px; }
.b-row:not(.first) .dep, .b-row:not(.first) .left .n { font-size: 44px; }
.b-row:not(.first) .dest .to { font-size: 28px; }
.b-row:not(.first) .dest .to small { font-size: 16px; }
.b-row:not(.first) .dest .route { font-size: 13px; margin-top: 4px; }
.b-row:not(.first) .left .u, .b-row:not(.first) .left .pre { font-size: 17px; }
.b-row:not(.first) .left.soon { font-size: 28px; }
.b-row:not(.first) .keito { font-size: 22px; min-width: 52px; padding: 6px 10px; }
.board.nishi .b-row:not(.first) .dest .via { font-size: 14px; margin-top: 2px; }
.board.nishi .b-row:not(.first) .where { font-size: 14px; margin-top: 2px; }

.x-row.first .x-dep .t { font-size: 84px; }
.x-row.first .x-dep .m { font-size: 26px; }
.x-row.first .x-arr .t { font-size: 64px; }
.x-row.first .x-train .t { font-size: 60px; }
.x-row.first .x-train .kind { font-size: 24px; padding: 7px 12px; }
.x-row.first .x-train .w { font-size: 20px; }
.x-row:not(.first) .x-dep .t { font-size: 40px; }
.x-row:not(.first) .x-dep .m { font-size: 16px; }
.x-row:not(.first) .x-dep .m .n { font-size: 20px; }
.x-row:not(.first) .x-arr .t { font-size: 32px; }
.x-row:not(.first) .x-train .t { font-size: 30px; }
.x-row:not(.first) .x-train .kind { font-size: 15px; padding: 4px 8px; }
.x-row:not(.first) .x-train .w { font-size: 14px; margin-top: 2px; }
.x-row:not(.first) .x-train .w b { font-size: 18px; }

/* 残り時間をいちばん目立たせる */
.left { color: #7fe6ff; text-shadow: 0 0 18px rgba(95, 216, 255, .35); }
.left .pre { color: #c9d6ff; }
.b-row.first .left .n { font-size: 116px; }
.b-row.first .left .u { font-size: 36px; }
.left.hurry { color: var(--alert); text-shadow: 0 0 18px rgba(255, 122, 69, .45); }
.left.hurry .pre { color: var(--alert); }

/* 先発の行は明るく、2便目以降は落ち着いた色に */
.b-row.first, .x-row.first {
  background: linear-gradient(90deg, rgba(255, 200, 61, .2), rgba(255, 255, 255, .06) 60%, rgba(255, 255, 255, .03));
}
.board.nishi .b-row.first {
  background: linear-gradient(90deg, rgba(230, 0, 51, .28), rgba(255, 255, 255, .06) 60%, rgba(255, 255, 255, .03));
}
.b-row:not(.first), .x-row:not(.first) { background: transparent !important; }
.b-row:not(.first) .dep, .x-row:not(.first) .x-dep .t { color: #c9a752; }
.b-row:not(.first) .dest .to, .x-row:not(.first) .x-arr .t, .x-row:not(.first) .x-train .t { color: #c3cbe0; }
.b-row:not(.first) .left:not(.hurry):not(.soon), .x-row:not(.first) .x-dep .m:not(.soon) {
  color: #6fb8d1; text-shadow: none;
}
.b-row:not(.first) .keito { opacity: .8; }

/* 米多比: JRの方面と行き先を大きく */
.x-cols .dir { font-size: 22px; letter-spacing: .05em; color: var(--text); }
.x-cols .dir small { font-size: 14px; color: var(--muted); margin-right: 6px; }
.x-train .w .to { font-size: 1.25em; font-weight: 900; color: var(--text); margin-right: 6px; }
.x-row:not(.first) .x-train .w .to { color: #c3cbe0; }

/* 縦長は全体をもう一段大きく */
.board.tall .b-row.first, .board.tall .x-row.first { min-height: 200px; }
.board.tall { --dep-w: 280px; }
.board.tall .b-row.first .dep, .board.tall .b-row.first .left .n { font-size: 110px; }
.board.tall .b-row.first .dest .to { font-size: 56px; }
.board.tall .b-row.first .dest .to.long { font-size: 40px; }
.board.tall .b-row.first .left .n { font-size: 84px; }
.board.tall .b-row.first .left .u { font-size: 28px; }
.board.tall .b-row.first .left .pre { font-size: 22px; }
.board.tall .b-row:not(.first), .board.tall .x-row:not(.first) { min-height: 110px; }
.board.tall .b-row:not(.first) .dep, .board.tall .b-row:not(.first) .left .n { font-size: 56px; }
.board.tall .b-row:not(.first) .dest .to { font-size: 36px; }

/* 狭い画面(プレビュー用) */
@container (max-width: 820px) {
  .b-head { padding: 18px 20px; flex-wrap: wrap; }
  .b-clock { text-align: left; }
  .b-logo { width: 48px; height: 48px; font-size: 26px; }
  .b-stop, .board.tall .b-stop { font-size: 28px; }
  .b-time, .board.tall .b-time { font-size: 44px; }
  .b-cols, .x-cols { display: none; }
  .b-row { grid-template-columns: auto minmax(0, 1fr) auto; padding: 14px 20px; gap: 4px 16px; min-height: 0; }
  .order { display: none; }
  .board.nishi .b-row { grid-template-columns: auto auto minmax(0, 1fr) auto; }
  .keito { font-size: 20px; min-width: 40px; padding: 6px 8px; }
  .dep, .left .n, .board.tall .dep, .board.tall .left .n { font-size: 40px; }
  .dest .to, .board.tall .dest .to { font-size: 24px; }
  .left.soon { font-size: 24px; }
  .x-row { grid-template-columns: 1fr 1fr; padding: 14px 20px; gap: 12px 16px; min-height: 0; }
  .x-train { border-left: 0; padding-left: 0; }
  .x-dep .t, .x-arr .t, .x-train .t { font-size: 34px; }
  .b-row.first, .x-row.first, .board.tall .b-row.first { min-height: 0; }
  .b-row.first .dep, .b-row.first .left .n,
  .board.tall .b-row.first .dep, .board.tall .b-row.first .left .n { font-size: 52px; }
  .b-row.first .dest .to, .board.tall .b-row.first .dest .to { font-size: 30px; }
  .b-row:not(.first), .x-row:not(.first), .board.tall .b-row:not(.first) { min-height: 0; padding-top: 8px; padding-bottom: 8px; }
  .b-row:not(.first) .dep, .b-row:not(.first) .left .n,
  .board.tall .b-row:not(.first) .dep, .board.tall .b-row:not(.first) .left .n { font-size: 28px; }
  .b-row:not(.first) .dest .to, .board.tall .b-row:not(.first) .dest .to { font-size: 18px; }
  .x-row.first .x-dep .t, .x-row.first .x-arr .t, .x-row.first .x-train .t { font-size: 44px; }
  .x-row:not(.first) .x-dep .t, .x-row:not(.first) .x-arr .t, .x-row:not(.first) .x-train .t { font-size: 26px; }
}

.st-key-langfix, .st-key-fit, .st-key-switcher { display: none !important; }

/* ディスプレイの高さいっぱいに広げる。行は余った高さを分け合う(先発は2倍) */
.board { display: flex; flex-direction: column; min-height: calc(100vh - 3rem - 24px); }
.board > .b-row, .board > .x-row { flex: 1 1 auto; }
.board > .b-row.first, .board > .x-row.first { flex-grow: 2; }
.board > .b-head, .board > .b-cols, .board > .x-cols, .board > .b-foot, .board > .sample { flex: none; }
.board > .b-empty { flex: 1; display: flex; flex-direction: column; justify-content: center; }

@keyframes blink { 50% { opacity: .2; } }
@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: .45; } }
</style>
"""


def setup(title, layout="wide"):
    """ページの最初に呼ぶ。サイドバーは閉じた状態で始める。

    layout: その設置場所のディスプレイの向き("wide" 横長 / "tall" 縦長)。
    URLに ?layout=tall などを付けると、そちらが優先される。
    """
    st.set_page_config(page_title=title, page_icon="🚌", layout="wide",
                       initial_sidebar_state="collapsed")
    st.session_state["layout"] = layout
    st.markdown(CSS, unsafe_allow_html=True)
    # Streamlit のページは「英語」扱いなので、Chrome が勝手に翻訳して文字が化ける
    # (先発→スタート など)。日本語のページで、翻訳しないよう印を付ける。
    with st.container(key="langfix"):
        components.html(
            """<script>
            const d = window.parent.document;
            d.documentElement.lang = "ja";
            d.documentElement.setAttribute("translate", "no");
            if (!d.querySelector('meta[name="google"]')) {
              const m = d.createElement("meta");
              m.name = "google"; m.content = "notranslate";
              d.head.appendChild(m);
            }
            </script>""",
            height=0,
        )


def orientation():
    layout = st.query_params.get("layout") or st.session_state.get("layout", "wide")
    return "tall" if layout == "tall" else "wide"


def row_count(default_wide=4, default_tall=7):
    """表示する本数。横長(1980×1280)は4本、縦長(1280×1980)は7本が画面に収まる。"""
    try:
        return int(st.query_params["rows"])
    except (KeyError, ValueError):
        return default_tall if orientation() == "tall" else default_wide


def koga_zip():
    """data/ からコガバスのGTFS(ZIP)を探す。"""
    zips = sorted(DATA_DIR.glob("*.zip"))
    koga = [z for z in zips if "kogabus" in z.name.lower()]
    return (koga or zips or [None])[0]


@st.cache_resource
def get_feed(zip_path: str):
    return load_feed(zip_path)


# ---------- HTMLの部品 ----------
def head_html(label, stop, now, tabs=None, suffix="のりば"):
    """ヘッダー。tabs = ("koga" か "nishi") を渡すと切り替えタブを出す。"""
    tab_html = ""
    if tabs:
        tab_html = (
            '<div class="tabs">'
            f'<span class="tab koga{" on" if tabs == "koga" else ""}">コガバス</span>'
            f'<span class="tab nishi{" on" if tabs == "nishi" else ""}">西鉄バス</span>'
            "</div>"
        )
    clock = ""
    if now is not None:
        clock = (
            '<div class="b-clock">'
            f'<div class="b-time num">{now:%H}<span class="colon">:</span>{now:%M}</div>'
            f'<div class="b-date">{now.month}月{now.day}日（{WEEKDAYS[now.weekday()]}）</div>'
            "</div>"
        )
    small = f"<small>{escape(suffix)}</small>" if suffix else ""
    return (
        '<div class="b-head"><div class="b-brand"><div class="b-logo">🚌</div><div>'
        f'<div class="b-label">{escape(label)}</div>'
        f'<div class="b-stop">{escape(stop)}{small}</div>{tab_html}'
        f"</div></div>{clock}</div>"
    )


def foot_html(now, note="※ 時刻表に基づく予定時刻です。道路状況により遅れる場合があります。"):
    return (
        f'<div class="b-foot"><span>{escape(note)}</span>'
        f'<span class="num">最終更新 {now:%H:%M:%S}</span></div>'
    )


def order_label(i):
    return ("先発", "次発", "次々発")[i] if i < 3 else f"{i + 1}番目"


def duration_html(m):
    """分数を「2時間19分」の形にする(60分未満は「19分」)。"""
    h, mm = divmod(m, 60)
    parts = []
    if h:
        parts.append(f'<span class="n">{h}</span><span class="u">時間</span>')
    if mm or not h:
        parts.append(f'<span class="n">{mm}</span><span class="u">分</span>')
    return "".join(parts)


def minutes_html(m):
    if m == 0:
        return '<div class="left soon">まもなく発車</div>'
    hurry = " hurry" if m <= 2 else ""      # 残り1〜2分は色を変えて知らせる
    return f'<div class="left num{hurry}"><span class="pre">あと</span>{duration_html(m)}</div>'


def long_class(dest):
    """先発の大きな文字で収まりきらない長い行き先には、小さめのクラスを付ける。"""
    return " long" if len(dest) > 7 else ""


def departures_html(deps):
    if not deps:
        return (
            '<div class="b-empty">本日の発車は終了しました'
            "<small>またのご利用をお待ちしております</small></div>"
        )
    html = [
        '<div class="b-cols"><span></span><span>発車時刻</span>'
        '<span>行き先</span><span class="r">発車まで</span></div>'
    ]
    for i, d in enumerate(deps):
        dest = escape(d["headsign"] or d["route"])
        route = escape(d["route"]) if d["headsign"] and d["route"] else ""
        html.append(
            f'<div class="b-row{" first" if i == 0 else ""}">'
            f'<span class="order">{order_label(i)}</span>'
            f'<div class="dep num">{d["time"]}</div>'
            f'<div class="dest"><div class="to{long_class(dest)}">{dest}<small>行</small></div>'
            + (f'<span class="route r-{route}">{route}</span>' if route else "")
            + f'</div>{minutes_html(d["minutes"])}</div>'
        )
    return "".join(html)


def koga_board_html(stop, routes, place, now, rows, tabs=None):
    feed = get_feed(str(koga_zip()))
    deps = next_departures(feed, stop, now=now, limit=rows, routes=routes)
    return (
        f'<div class="board koga notranslate {orientation()}" translate="no">'
        + head_html(f"{place} ・ コガバス 発車案内", stop, now, tabs=tabs)
        + departures_html(deps)
        + foot_html(now)
        + "</div>"
    )


# ---------- 西鉄バスナビ風のデザイン(西鉄の画面と交互に出しても違和感がないように) ----------
# 西鉄「バスナビジョン」のテンプレート(bnn.css / bnn16.css / bnn18.css)の色・大きさに合わせている。
#   18: 横長。見出しにタイトル、左右2列 × 5行(青柳四つ角と同じ)
#   16: 縦長。1列 × 15行(コスモス館前・JR古賀駅東口と同じ)
NNR_CSS = """
<style>
:root { --frame: #d96a00; --sub: #ffd54a; }   /* 自分たちの画面の色(西鉄の青と区別するためオレンジ) */
.stApp { background: var(--frame) !important; }
.nnr .brand { display: inline-block; background: #fff; color: var(--frame); padding: 0 .3em; margin-right: .3em;
  border-radius: .15em; line-height: 1.1em; }
[data-testid="stMainBlockContainer"], .block-container { padding: 0 !important; }
[data-testid="stVerticalBlock"] { gap: 0 !important; }
.nnr, .nnr table, .nnr th, .nnr td { font-family: Helvetica, Meiryo, "MS PGothic", sans-serif; }
.nnr { background: var(--frame); color: #fff; font-weight: bold; }
.nnr table { margin: 0; padding: 0; table-layout: fixed; font-weight: bold; border-collapse: collapse; }
.nnr th, .nnr td { margin: 0; padding: 0; }
.nnr .disp { border: 0; width: 100%; }
.nnr .header_title { background: var(--frame); color: #fff; vertical-align: bottom; text-align: left; }
.nnr .text_title { float: left; text-align: left; }
.nnr .text_time { text-align: right; }
.nnr .va_top { vertical-align: top; }
.nnr .list { border: 0; width: 100%; }
.nnr .list th { background: #fff; color: var(--frame); border: 4px solid var(--frame); vertical-align: middle; line-height: 1em;
  text-align: center; }
.nnr .list td { border: 4px solid var(--frame); vertical-align: middle; overflow: hidden; background: #000;
  text-align: left; color: #fff; }
.nnr .list td.bin, .nnr .list td.txtct { text-align: center; }
.nnr .now.long { white-space: nowrap; }
.nnr.t16 .now.long { font-size: 26px; }
.nnr.t18 .now.long { font-size: 28px; }
.nnr .bin { text-align: center; color: #fff; line-height: 1.05em; }
.nnr .yki { color: #fff; line-height: 1em; display: inline-block; overflow: hidden; white-space: nowrap; }
.nnr .kiy { color: var(--sub); line-height: 1em; display: inline-block; overflow: hidden; white-space: nowrap; }
.nnr .jkn { color: #fff; line-height: 1em; }
.nnr .now { color: var(--sub); line-height: 1em; }
.nnr .txtct { text-align: center; }
.nnr .credit { font-size: 20px; line-height: 1.4em; padding: 4px 8px; color: #fff; font-weight: normal; }
.nnr .left { margin-right: 3px; }
.nnr .right { margin-left: 3px; }

/* テンプレート16(縦長) */
.nnr.t16 .header_title { font-size: 34px; height: 50px; line-height: 1em; }
.nnr.t16 .i_bin { width: 155px; font-size: 20px; }
.nnr.t16 .i_yk { font-size: 20px; }
.nnr.t16 .i_jkn { width: 255px; font-size: 20px; }
.nnr.t16 .bin { font-size: 30px; }
.nnr.t16 .yki { font-size: 50px; height: 1em; }
.nnr.t16 .kiy { font-size: 34px; height: 1em; }
.nnr.t16 .jkn { font-size: 60px; }
.nnr.t16 .now { font-size: 30px; }
.nnr.t16 .gyo { height: 119px; }

/* テンプレート18(横長) */
.nnr.t18 .disp { width: 1920px; }
.nnr.t18 .header_title { font-size: 48px; height: 96px; line-height: 1em; padding: 6px 6px 0 6px; }
.nnr.t18 .list th { height: 34px; font-size: 26px; }
.nnr.t18 .i_bin { width: 190px; font-size: 26px; }
.nnr.t18 .i_yk { font-size: 26px; }
.nnr.t18 .i_jkn { width: 220px; font-size: 24px; }
.nnr.t18 .bin { font-size: 36px; }
.nnr.t18 .yki { font-size: 54px; }
.nnr.t18 .kiy { font-size: 30px; }
.nnr.t18 .jkn { font-size: 66px; }
.nnr.t18 .now { font-size: 40px; }
.nnr.t18 .gyo { height: 182px; }
</style>
"""


# 画面の大きさに合わせて発車標全体を拡大・縮小し、いつも1画面に収める(スクロールさせない)。
# Streamlit は定期的に表を描き直すので、0.3秒ごとに大きさを合わせ直す。
FIT_JS = """
<script>
(function () {
  const w = window.parent, d = w.document;
  if (w.__fitInstalled) return;
  w.__fitInstalled = true;
  const css = d.createElement("style");
  css.textContent = "html, body, .stApp, [data-testid='stMain'], [data-testid='stAppViewContainer']" +
                    " { overflow: hidden !important; }";
  d.head.appendChild(css);
  // 大きさの決め方: バスの入っている行(とお知らせ)が全部見える範囲で、できるだけ大きく表示する。
  // 西鉄に合わせて足している空の行(.pad)は、入りきらなければ表示しない。
  const fit = () => {
    const el = d.querySelector(".nnr");
    if (!el) return;
    const designW = Number(el.dataset.w) || 1920;    // そのレイアウトの本来の横幅
    el.style.transform = "none";
    el.style.width = designW + "px";
    el.querySelectorAll("tr.pad").forEach(r => { r.style.display = ""; });
    const top = el.getBoundingClientRect().top;
    let needH = 0;                                   // 必ず見せたい部分の高さ
    el.querySelectorAll(".header_title, tr:not(.pad) > td.gyo, .msg").forEach(c => {
      needH = Math.max(needH, c.getBoundingClientRect().bottom - top);
    });
    if (!needH) return;
    // 出典の行は空の行の下にあるので、高さだけ別に足す(空の行を消すと上に詰まる)
    const credit = el.querySelector(".credit");
    const creditH = credit ? credit.offsetHeight : 0;
    needH += 8 + creditH;                            // 8 は表の下の枠線のぶん
    const s = Math.min(w.innerWidth / designW, w.innerHeight / needH);
    el.style.width = (w.innerWidth / s) + "px";      // 拡大・縮小したあとも横幅いっぱいになるように
    const limit = w.innerHeight / s - creditH - 8;
    el.querySelectorAll("tr.pad").forEach(r => {     // はみ出す空の行は消す
      if (r.getBoundingClientRect().bottom - top > limit) r.style.display = "none";
    });
    el.style.transformOrigin = "top left";
    el.style.transform = "scale(" + s + ")";
  };
  w.addEventListener("resize", fit);
  w.setInterval(fit, 300);
  fit();
})();
</script>
"""


def fit_to_screen():
    with st.container(key="fit"):
        components.html(FIT_JS, height=0)


def nnr_left(m):
    """西鉄の「現在地」の位置に出す、発車までの時間。"""
    if m == 0:
        return "まもなく発車"
    h, mm = divmod(m, 60)
    if not h:
        return f"あと{mm}分"
    return f"あと{h}時間{mm}分" if mm else f"あと{h}時間"


def nnr_rows(deps, count):
    """count 行ぶんの <tr>。足りない分は西鉄と同じく空の黒い行で埋める。"""
    rows = []
    for d in deps[:count]:
        route = escape(d["route"])
        dest = escape(d["headsign"] or d["route"])
        rows.append(
            f'<tr><td class="gyo bin">{route}</td>'
            f'<td class="gyo"><span class="yki">{dest}</span><br/><span class="kiy">&#12288;</span></td>'
            f'<td class="gyo txtct"><span class="jkn">{escape(d["time"])}</span><br/>'
            f'<span class="now{" long" if d["minutes"] >= 60 else ""}">{nnr_left(d["minutes"])}</span></td></tr>'
        )
    while len(rows) < count:
        rows.append('<tr class="pad"><td class="gyo bin"></td><td class="gyo"></td><td class="gyo txtct"></td></tr>')
    return "".join(rows)


def nnr_list(deps, count, side):
    return (
        f'<table class="list {side}"><tr>'
        '<th class="i_bin">路線</th><th class="i_yk">行先</th><th class="i_jkn">所定時刻 発車まで</th></tr>'
        + nnr_rows(deps, count)
        + "</table>"
    )


def nnr_board_html(site, now, template):
    feed = get_feed(str(koga_zip()))
    per_col, cols = (5, 2) if template == 18 else (15, 1)
    deps = next_departures(feed, site["stop"], now=now, limit=per_col * cols, routes=site["routes"])
    title = f'<span class="brand">コガバス</span>接近情報<br />{escape(site["stop"])}'
    head = (
        f'<tr><th colspan="{cols}" class="header_title">'
        f'<div class="text_title">{title}</div>'
        f'<div class="text_time">{now:%H:%M} 現在の状況</div></th></tr>'
    )
    if cols == 2:
        body = (
            f'<tr><td class="va_top">{nnr_list(deps[:per_col], per_col, "left")}</td>'
            f'<td class="va_top">{nnr_list(deps[per_col:], per_col, "right")}</td></tr>'
        )
    else:
        body = f'<tr><td class="va_top">{nnr_list(deps, per_col, "left")}</td></tr>'
    # オープンデータ(CC BY 4.0)の条件として、出典を表示する
    credit = '<div class="credit">時刻表データ出典: 古賀市「コガバス」GTFS-JP(CC BY 4.0)</div>'
    return (
        f'<div class="nnr t{template} notranslate" translate="no" data-w="{1920 if template == 18 else 1280}">'
        f'<table class="disp">{head}{body}</table>{credit}</div>'
    )


# ---------- URLだけで西鉄バスナビと切り替える(青柳・コスモス館・古賀駅) ----------
# 駅員さんがURLを開くと(自動で。ポップアップが許可されていなければ「表示開始」ボタンで)新しいウィンドウが開き、その中身を
# 「コガバスのページ」⇔「西鉄バスナビ(元のURLのまま)」と交互に移動させる。
# 西鉄のページは埋め込まず、そのまま開くだけなので一切変更しない。
#   ・コガバスに戻ったときは、時刻表が表示されるのを待ってから数え始める
#   ・このウィンドウは表示用ウィンドウの裏に隠れるため、Chrome の「裏のウィンドウのタイマーを
#     遅くする」仕組みの影響を受けない Web Worker で時間を数える
CONTROLLER_JS = """
<script>
(function () {
  const w = window.parent, d = w.document;
  w.__swConf = __CONF__;
  if (w.__swInstalled) return;
  w.__swInstalled = true;
  const s = d.createElement("script");
  s.textContent = `(() => {
    const conf = () => window.__swConf;
    const css = document.createElement("style");
    css.textContent = \\`
      #sw-panel { position: fixed; inset: 0; z-index: 99999; display: flex; align-items: center;
        justify-content: center; background: rgba(0,0,0,.55);
        font-family: Helvetica, Meiryo, "MS PGothic", sans-serif; }
      #sw-panel .box { background: #fff; color: #222; border-radius: 16px; padding: 32px 40px;
        max-width: 640px; text-align: center; box-shadow: 0 20px 60px rgba(0,0,0,.4); }
      #sw-panel h2 { margin: 0 0 12px; font-size: 28px; color: #d96a00; }
      #sw-panel p { margin: 8px 0; font-size: 18px; line-height: 1.6; }
      #sw-panel button { margin-top: 18px; font-size: 24px; font-weight: bold; padding: 14px 36px;
        border: 0; border-radius: 10px; background: #d96a00; color: #fff; cursor: pointer; }
      #sw-panel button.sub { background: #888; font-size: 16px; padding: 8px 20px; margin-left: 8px; }
      #sw-panel.hidden { display: none; }
    \\`;
    document.head.appendChild(css);
    const panel = document.createElement("div");
    panel.id = "sw-panel";
    document.body.appendChild(panel);

    let win = null, phase = "", due = 0, waiting = false, waitUntil = 0;
    const kogaUrl = () => {
      const t = window.top.location;
      return t.origin + t.pathname + "?display=1";
    };
    // 表示用ウィンドウのコガバスのページに、時刻表(.nnr)が出たかを調べる(枠の中も探す)
    const rendered = (doc) => {
      try {
        if (doc.querySelector(".nnr")) return true;
        for (const f of doc.querySelectorAll("iframe")) {
          try { if (f.contentDocument && rendered(f.contentDocument)) return true; } catch (e) {}
        }
      } catch (e) {}
      return false;
    };
    const showStart = () => {
      panel.className = "";
      panel.innerHTML = '<div class="box"><h2>西鉄バスと切り替えて表示</h2>' +
        '<p>「表示開始」を押すと新しいウィンドウが開き、コガバスと西鉄バスの案内が' +
        conf().sec + '秒ごとに切り替わります。</p>' +
        '<p>開いたウィンドウで <b>F11</b> を押すと全画面になります。</p>' +
        '<button id="sw-start">表示開始</button>' +
        '<button id="sw-close" class="sub">このまま見る</button></div>';
      panel.querySelector("#sw-start").onclick = start;
      panel.querySelector("#sw-close").onclick = () => { panel.className = "hidden"; };
    };
    const showRunning = () => {
      panel.className = "";
      panel.innerHTML = '<div class="box"><h2>表示中です</h2>' +
        '<p><b>このウィンドウは閉じないでください。</b>閉じると切り替えが止まります。</p>' +
        '<p>表示用のウィンドウで <b>F11</b> を押すと全画面になります。</p>' +
        '<p style="font-size:15px;color:#666">長時間つけておくパソコンでは、Chrome の設定 →「パフォーマンス」→' +
        '「常にアクティブにしておくサイト」に <b>streamlit.app</b> を追加しておくと、' +
        '裏にあるこのウィンドウが休止せず安心です。</p>' +
        '<button id="sw-stop" class="sub">停止する</button></div>';
      panel.querySelector("#sw-stop").onclick = stop;
    };
    const go = (p) => {
      phase = p;
      if (p === "koga") {
        win.location.href = kogaUrl();
        waiting = true; waitUntil = Date.now() + 15000;   // 表示されるまで待つ(最大15秒)
      } else {
        win.location.href = conf().nnr;
        waiting = false; due = Date.now() + (conf().sec + 1) * 1000;  // 読み込みの1秒ぶん長めに
      }
    };
    const tick = () => {
      if (!win) return;
      if (win.closed) { stop(); return; }
      const now = Date.now();
      if (phase === "koga" && waiting) {
        let ok = false;
        try { ok = rendered(win.document); } catch (e) {}
        if (ok || now > waitUntil) { waiting = false; due = now + conf().sec * 1000; }
        return;
      }
      if (now >= due) go(phase === "koga" ? "nnr" : "koga");
    };
    // 裏に回っても遅くならない Web Worker の時計
    const worker = new Worker(URL.createObjectURL(new Blob(
      ["setInterval(() => postMessage(0), 200);"], { type: "text/javascript" })));
    worker.onmessage = tick;
    // ポップアップがブロックされたとき(そのパソコンで初めて開いたとき)の案内
    const showBlocked = () => {
      panel.className = "";
      panel.innerHTML = '<div class="box"><h2>ポップアップを許可してください</h2>' +
        '<p>表示用のウィンドウを開けませんでした。<b>このパソコンで最初の1回だけ</b>、' +
        '次の設定をしてください。</p>' +
        '<p>アドレスバーの右に出ている <b>ポップアップのアイコン</b> を押し、' +
        '「<b>常に許可する</b>」を選んで「完了」。<br>次からは、URLを開くだけで自動で始まります。</p>' +
        '<button id="sw-start">今すぐ表示開始</button>' +
        '<button id="sw-close" class="sub">このまま見る</button></div>';
      panel.querySelector("#sw-start").onclick = start;
      panel.querySelector("#sw-close").onclick = () => { panel.className = "hidden"; };
    };
    function start(auto) {
      win = window.open(kogaUrl(), "koga-display",
        "popup=yes,left=0,top=0,width=" + screen.availWidth + ",height=" + screen.availHeight);
      if (!win) { showBlocked(); return; }
      phase = "koga"; waiting = true; waitUntil = Date.now() + 15000;
      showRunning();
    }
    function stop() {
      if (win && !win.closed) win.close();
      win = null; phase = "";
      showStart();
    }
    // URLを開いたら自動で始める(ポップアップが許可されていなければ案内を出す)
    start(true);
  })();`;
  d.body.appendChild(s);
})();
</script>
"""


def switch_controller(site):
    """URLに ?display=1 が付いていない(=駅員さんが開いた)ときだけ、「表示開始」を出す。"""
    if st.query_params.get("display") or not site.get("nishitetsu_url"):
        return
    conf = {"nnr": site["nishitetsu_url"], "sec": SWITCH_SECONDS}
    with st.container(key="switcher"):
        components.html(CONTROLLER_JS.replace("__CONF__", json.dumps(conf)), height=0)


# ---------- 切り替え表示(青柳・コスモス館・古賀駅) ----------
def site_page(site):
    """コガバスの発車標のページ。URLを開くと表示用ウィンドウが開き、
    西鉄バスナビ(元のページのまま)と交互に表示される(switch_controller)。"""
    setup(f'{site["place"]} 発車案内', site.get("layout", "wide"))
    if koga_zip() is None:
        st.error("data フォルダにコガバスのGTFS(ZIP)を入れてください(README参照)")
        st.stop()

    if site.get("nnr_template"):
        # 西鉄バスナビと交互に表示するので、西鉄と同じ並びのデザインでコガバスを表示する
        st.markdown(NNR_CSS, unsafe_allow_html=True)
        fit_to_screen()
        switch_controller(site)

        @st.fragment(run_every=REFRESH_SECONDS)
        def koga_nnr():
            st.markdown(nnr_board_html(site, datetime.now(JST), site["nnr_template"]),
                        unsafe_allow_html=True)

        koga_nnr()
        return

    # nnr_template を消したときの独自デザイン(切り替えなし)
    rows = row_count()

    @st.fragment(run_every=REFRESH_SECONDS)
    def koga_only():
        now = datetime.now(JST)
        st.markdown(
            koga_board_html(site["stop"], site["routes"], site["place"], now, rows, tabs="koga"),
            unsafe_allow_html=True,
        )

    koga_only()

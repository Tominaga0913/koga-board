"""トップページ(4つの設置場所へのリンク)"""
import streamlit as st

from board import setup

setup("コガバス発車標")

st.markdown(
    """
<style>
.menu-title { font-family: 'Noto Sans JP', sans-serif; color: var(--text); margin: 8px 0 24px; }
.menu-title h1 { font-size: 40px; font-weight: 900; margin: 0; color: var(--text); }
.menu-title p { color: var(--muted); margin: 6px 0 0; }
[data-testid="stPageLink"] a {
  background: var(--panel); border: 1px solid var(--line); border-radius: 16px;
  padding: 20px 24px !important;
}
[data-testid="stPageLink"] a:hover { border-color: var(--amber); }
[data-testid="stPageLink"] p { font-size: 22px !important; font-weight: 700; color: var(--text) !important; }
</style>
<div class="menu-title notranslate" translate="no"><h1>🚌 コガバス発車標</h1>
<p>表示したい設置場所を選んでください。URLの末尾に <code>?layout=tall</code> を付けると縦長ディスプレイ用になります。</p></div>
""",
    unsafe_allow_html=True,
)

st.page_link("pages/1_米多比.py", label="1. 米多比郵便局 — 西鉄バス → JR古賀駅 乗り継ぎ案内")
st.page_link("pages/2_青柳.py", label="2. 青柳郵便局 — コガバス(JR古賀線) ⇔ 西鉄バス")
st.page_link("pages/3_コスモス館.py", label="3. コスモス館 — コガバス(JR古賀線・小竹線) ⇔ 西鉄バス")
st.page_link("pages/4_古賀駅.py", label="4. JR古賀駅 自由通路 — コガバス(JR古賀線) ⇔ 西鉄バス")

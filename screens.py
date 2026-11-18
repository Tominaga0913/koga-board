"""画面の一覧と、表示する画面の切り替え。

app.py(メニュー付き)と、サーバー用の site_*.py(1か所だけ)の両方から使う。
新しい画面を足すときはここに1行追加します。
"""
import streamlit as st

# 指定名: (ファイル, タイトル, URL)
SCREENS = {
    "yatabi": ("pages/1_米多比.py", "米多比郵便局", "米多比"),
    "aoyagi": ("pages/2_青柳.py", "青柳郵便局", "青柳"),
    "cosmos": ("pages/3_コスモス館.py", "コスモス館", "コスモス館"),
    "koga": ("pages/4_古賀駅.py", "JR古賀駅 自由通路", "古賀駅"),
}


def run(only=None):
    """only に指定名を渡すとその画面だけ(メニューや他の画面には行けない)。省略するとメニュー付き。"""
    if only in SCREENS:
        path, title, _ = SCREENS[only]
        pages = [st.Page(path, title=title, icon="🚌", default=True)]
    else:
        pages = [st.Page("home.py", title="メニュー", icon="🏠", default=True)] + [
            st.Page(path, title=title, icon="🚌", url_path=url) for path, title, url in SCREENS.values()
        ]
    st.navigation(pages, position="hidden").run()

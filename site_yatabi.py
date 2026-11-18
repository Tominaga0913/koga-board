"""サーバー(Streamlit Community Cloud)用の入口: 米多比郵便局 の画面だけを表示する。

Streamlit Cloud でアプリを作るとき、Main file path に site_yatabi.py を指定する。
"""
from screens import run

run("yatabi")

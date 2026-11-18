"""サーバー(Streamlit Community Cloud)用の入口: 青柳郵便局 の画面だけを表示する。

Streamlit Cloud でアプリを作るとき、Main file path に site_aoyagi.py を指定する。
"""
from screens import run

run("aoyagi")

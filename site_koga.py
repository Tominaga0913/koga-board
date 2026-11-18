"""サーバー(Streamlit Community Cloud)用の入口: JR古賀駅 自由通路 の画面だけを表示する。

Streamlit Cloud でアプリを作るとき、Main file path に site_koga.py を指定する。
"""
from screens import run

run("koga")

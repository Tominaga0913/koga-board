"""コガバス発車標(入口)

起動:  streamlit run app.py
       → メニューから4つの画面を選べる

1か所だけ表示:  streamlit run app.py -- aoyagi
       → 青柳の画面だけを表示(メニューや他の画面には行けない)
       指定できるのは yatabi / aoyagi / cosmos / koga

サーバー(Streamlit Community Cloud)では、場所ごとに site_*.py を入口にする。
画面の一覧は screens.py にあります。
"""
import sys

from screens import run

run(sys.argv[1] if len(sys.argv) > 1 else None)

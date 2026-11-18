"""サーバー(Streamlit Community Cloud)のアプリが休止しないよう、定期的に開いて起こす。

GitHub Actions(.github/workflows/keep-awake.yml)から数時間ごとに動く。
kiosk_urls.txt に書いた4つのURLを、画面に出ないブラウザで開き、
休止していたら「起こす」ボタンを押して、時刻表が表示されるまで待つ。

手元で試すとき:  pip install playwright && playwright install chromium && python keep_awake.py
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

URLS_FILE = Path(__file__).parent / "kiosk_urls.txt"
WAKE_TEXT = "get this app back up"   # 休止中の画面のボタン「Yes, get this app back up!」


def read_urls():
    urls = []
    for line in URLS_FILE.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or ": " not in line:
            continue
        urls.append(line.split(": ", 1)[1].strip())
    return urls


def board_shown(page):
    """アプリの中(枠の中も含む)に時刻表(.nnr)が出ているか。"""
    for frame in page.frames:
        try:
            if frame.query_selector(".nnr"):
                return True
        except Exception:
            pass
    return False


def wake(page, url):
    page.goto(url, wait_until="domcontentloaded", timeout=60_000)
    woke = False
    for _ in range(36):                       # 最大およそ3分待つ
        if board_shown(page):
            return "表示OK" + ("(休止から起こしました)" if woke else "")
        button = page.get_by_role("button", name=WAKE_TEXT)
        if not woke and button.count():
            button.first.click()
            woke = True
        page.wait_for_timeout(5_000)
    return "表示を確認できませんでした"


def main():
    urls = read_urls()
    failed = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for url in urls:
            page = browser.new_page(viewport={"width": 1280, "height": 1980})
            try:
                result = wake(page, url)
            except Exception as e:                # 1つ失敗しても残りは続ける
                result = f"エラー: {e}"
            if not result.startswith("表示OK"):
                failed += 1
            print(f"{url}  {result}", flush=True)
            page.close()
        browser.close()
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()

# -*- coding: utf-8 -*-
"""ココナラ「2026年の星の流れ」納品用PDFを1コマンドで作る。
（公開サイト不要・手元で生成。買い手の生年月日を入れてPDF納品するだけ）

使い方:
  python3 gen_sr_pdf.py "お名前" 1985-04-01 12:00 東京
  python3 gen_sr_pdf.py "お名前" 1985-04-01            # 時刻不明→12:00・出生地→東京
  python3 gen_sr_pdf.py "お名前" 1985-04-01 14:30 新潟県十日町市

→ deliverables/ にPDFができる。それをココナラのトークルームに添付して納品。
"""
import sys, os, base64
import moonlog_astrology as ma

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "deliverables")
os.makedirs(OUT_DIR, exist_ok=True)


# 章タイトル（検索キー）— PDFしおり目次の見出し。実際の各章の最後の出現ページに飛ばす
# (検索キー, しおり表示名)
_SECTIONS = [
    ("からの変化", "前年からの変化"),
    ("総合的な今年の星読み", "総合的な今年の星読み"),
    ("今年のあなた", "今年のあなた（太陽）"),
    ("今年の仕事運", "今年の仕事運"),
    ("感情・プライベート・家族", "感情・プライベート・家族（月）"),
    ("仕事・学び・コミュニケーション", "仕事・学び・コミュニケーション（水星）"),
    ("愛・パートナーシップ・喜び", "愛・パートナーシップ・喜び（金星）"),
    ("行動・情熱・エネルギー", "行動・情熱・エネルギー（火星）"),
    ("成長・チャンス・広がり", "成長・チャンス・広がり（木星）"),
    ("課題・成熟・乗り越え方", "課題・成熟・乗り越え方（土星）"),
]


def _add_bookmarks(pdf_path):
    """PDFに目次（しおり）を追加。各章タイトルの最後の出現ページ＝本文見出しへ飛ばす。"""
    try:
        import fitz
        doc = fitz.open(pdf_path)
        toc = []
        for key, label in _SECTIONS:
            last = None
            for pno in range(doc.page_count):
                if doc[pno].search_for(key):
                    last = pno
            if last is not None:
                toc.append([1, label, last + 1])
        if toc:
            doc.set_toc(toc)
            tmp = pdf_path + ".tmp"
            doc.save(tmp, garbage=4, deflate=True)
            doc.close()
            os.replace(tmp, pdf_path)
            print(f"   しおり目次 {len(toc)}項目を追加")
        else:
            doc.close()
    except Exception as e:
        print(f"   （しおり追加はスキップ: {e}）")


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(1)
    name = sys.argv[1].strip() or "あなた"
    y, mo, d = [int(x) for x in sys.argv[2].split("-")]
    if len(sys.argv) >= 4 and ":" in sys.argv[3]:
        hh, mn = [int(x) for x in sys.argv[3].split(":")[:2]]
        time_known = True
    else:
        hh, mn = 12, 0
        time_known = False
    city = sys.argv[4] if len(sys.argv) >= 5 else (sys.argv[3] if len(sys.argv) >= 4 and ":" not in sys.argv[3] else "東京")

    lat, lng, tz = ma.resolve_location(city)
    print(f"対象: {name} / {y}-{mo:02d}-{d:02d} {hh:02d}:{mn:02d}"
          f"{'（時刻不明=12:00で作成）' if not time_known else ''} / {city}({lat:.2f},{lng:.2f})")

    html = ma.generate_solar_return_html(name, y, mo, d, hh, mn, city,
                                         lat=lat, lng=lng, tz_str=tz)  # sample=False=フル版

    safe = "".join(c for c in name if c.isalnum() or c in "ぁ-んァ-ヶ一-龯ー")[:20] or "report"
    out = os.path.join(OUT_DIR, f"{safe}_2026星読み.pdf")

    from playwright.sync_api import sync_playwright
    b64 = base64.b64encode(html.encode("utf-8")).decode("ascii")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            page = browser.new_page()
            page.goto(f"data:text/html;base64,{b64}", wait_until="networkidle", timeout=40000)
            page.wait_for_timeout(600)
            page.pdf(path=out, format="A4", print_background=True,
                     margin={"top": "12mm", "bottom": "12mm", "left": "10mm", "right": "10mm"})
        finally:
            browser.close()

    _add_bookmarks(out)
    print(f"\n✅ 完成: {out}")
    print("   → これをココナラのトークルームに添付して納品してください。")


if __name__ == "__main__":
    main()

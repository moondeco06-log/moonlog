# -*- coding: utf-8 -*-
"""ココナラ②「仕事・お金・恋愛 3分野レポート」納品用PDFを1コマンドで作る。

使い方:
  python3 gen_field_pdf.py "お名前" 1985-04-01 12:00 東京
  python3 gen_field_pdf.py "お名前" 1985-04-01            # 時刻不明→12:00・出生地→東京

→ deliverables/ にPDFができる。ココナラのトークルームに添付して納品。
"""
import sys, os, base64
import moonlog_astrology as ma
import moonlog_field_report as mf

ROOT = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(ROOT, "deliverables")
os.makedirs(OUT_DIR, exist_ok=True)


# 章タイトル（検索キー）— PDFしおり目次の見出し。実際の各章の最後の出現ページに飛ばす
# (検索キー, しおり表示名)
_SECTIONS = [
    ("第1章", "第1章 仕事・天職"),
    ("第2章", "第2章 お金・豊かさ"),
    ("第3章", "第3章 恋愛・パートナーシップ"),
    ("3つの分野をつなぐ", "まとめ 3つの分野をつなぐもの"),
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

    html = mf.generate_field_report_html(name, y, mo, d, hh, mn, city,
                                         lat=lat, lng=lng, tz_str=tz)  # sample=False=フル版

    safe = "".join(c for c in name if c.isalnum() or c in "ぁ-んァ-ヶ一-龯ー")[:20] or "report"
    out = os.path.join(OUT_DIR, f"{safe}_3分野レポート.pdf")

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

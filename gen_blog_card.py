"""12星座ブログサムネ一括生成。
yagi-2026.png（旧版）の背景＝グラデ＋月＋星をそのまま再利用し、
文字だけ大きく：星座名＋2026＋moonlog（キャッチフレーズなし）"""
from PIL import Image, ImageDraw, ImageFont

FONT = "/Users/mitsuinatsuki/Library/Fonts/花とちょうちょ.ttf"
BASE = "/Users/mitsuinatsuki/Documents/code_yousai/static/images/blog"
W, H = 1200, 630

NAVY = (23, 55, 100)
GOLD = (164, 120, 28)
GRAY = (130, 140, 162)

SIGNS = {
    "ohitsuji-2026": "牡羊座",
    "oushi-2026": "牡牛座",
    "futago-2026": "双子座",
    "kani-2026": "蟹座",
    "shishi-2026": "獅子座",
    "otome-2026": "乙女座",
    "tenbin-2026": "天秤座",
    "sasori-2026": "蠍座",
    "ite-2026": "射手座",
    "yagi-2026": "山羊座",
    "mizugame-2026": "水瓶座",
    "uo-2026": "魚座",
}

# ── テンプレ背景を山羊座旧版から作る ──
src = Image.open(f"{BASE}/yagi-2026.png").convert("RGB")
# 左端の列（文字なし）から縦グラデを全幅に展開
col = src.crop((8, 0, 9, H)).resize((W, H))
bg_template = col.copy()
# 右側ストリップ（月＋星・文字なし）をそのまま貼り戻す
strip_x = 820
bg_template.paste(src.crop((strip_x, 0, W, H)), (strip_x, 0))

fn_sign = ImageFont.truetype(FONT, 175)
fn_year = ImageFont.truetype(FONT, 85)
fn_brand = ImageFont.truetype(FONT, 32)

for slug, sign in SIGNS.items():
    img = bg_template.copy()
    d = ImageDraw.Draw(img)
    d.text((W // 2, 250), sign, font=fn_sign, fill=NAVY, anchor="mm")
    d.text((W // 2, 450), "2026", font=fn_year, fill=GOLD, anchor="mm")
    d.text((W // 2, 575), "moonlog", font=fn_brand, fill=GRAY, anchor="mm")
    img.save(f"{BASE}/{slug}.png")
    print("saved", slug)

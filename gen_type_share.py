# -*- coding: utf-8 -*-
"""月タイプ診断 シェア画像ジェネレーター（Instagramストーリーズ縦型 1080x1920）。
診断結果ページの「シェアする」用。動物カード＋タイプ名＋診断への誘導を1枚に。
出力: static/images/types/share/<moon_key>.png （12タイプ）
使い方: python3 gen_type_share.py        （全タイプ生成）
        python3 gen_type_share.py Gem    （1タイプだけ）
"""
import os, sys
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = os.path.dirname(os.path.abspath(__file__))
CARD_DIR = os.path.join(ROOT, "static", "images", "types", "final")
OUT_DIR = os.path.join(ROOT, "static", "images", "types", "share")
os.makedirs(OUT_DIR, exist_ok=True)

F_HANA = "/Users/mitsuinatsuki/Library/Fonts/花とちょうちょ.ttf"
F_GOTHIC = "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc"

# ブランドカラー（moonlog_types.py と合わせる）
CREAM = (250, 246, 236)
NAVY = (34, 50, 79)
GOLD = (189, 154, 72)
GRAY = (123, 122, 114)

W, H = 1080, 1920

# moonlog_types.TYPE_DATA から必要分（animal / img / name）。重複保持を避けず最小限で持つ。
import moonlog_types as MT
SIGN_JP = MT.SIGN_JP
TYPE_DATA = MT.TYPE_DATA


def font(path, size):
    return ImageFont.truetype(path, size)


def text_w(draw, s, f):
    b = draw.textbbox((0, 0), s, font=f)
    return b[2] - b[0]


def draw_center(draw, cx, y, s, f, fill):
    b = draw.textbbox((0, 0), s, font=f)
    draw.text((cx - (b[2] - b[0]) / 2 - b[0], y), s, font=f, fill=fill)
    return b[3] - b[1]


def fit_font(draw, s, path, start, maxw):
    """maxw に収まるまでフォントサイズを下げて返す。"""
    size = start
    while size > 40:
        f = font(path, size)
        if text_w(draw, s, f) <= maxw:
            return f
        size -= 4
    return font(path, size)


def build(key):
    t = TYPE_DATA[key]
    sign_jp = SIGN_JP.get(key, key)
    img = Image.new("RGB", (W, H), CREAM)
    d = ImageDraw.Draw(img)
    cx = W // 2

    # 外枠（細い金の内フレーム＝カードと同じ世界観）
    m = 36
    d.rectangle([m, m, W - m, H - m], outline=GOLD, width=3)

    # 上部ブランド
    draw_center(d, cx, 96, "moonlog", font(F_HANA, 76), NAVY)
    draw_center(d, cx, 210, "― 月タイプ診断 ―", font(F_GOTHIC, 38), GOLD)

    # 動物カード（円形エンブレム）を中央に
    card = Image.open(os.path.join(CARD_DIR, t["img"])).convert("RGBA")
    SZ = 800
    card = card.resize((SZ, SZ), Image.LANCZOS)
    img.paste(card, (cx - SZ // 2, 300), card)

    # タイプ名（大・花とちょうちょ）
    name = t["name"]
    fn = fit_font(d, name, F_HANA, 128, W - 200)
    draw_center(d, cx, 1170, name, fn, NAVY)

    # サブ：○○座の月 ・ 動物
    draw_center(d, cx, 1340, f"{sign_jp}の月  ・  {t['animal']}", font(F_GOTHIC, 50), GRAY)

    # 金の細い区切り
    d.line([cx - 180, 1450, cx + 180, 1450], fill=GOLD, width=2)

    # 下部 誘導ボックス
    bx0, by0, bx1, by1 = 110, 1540, W - 110, 1810
    d.rounded_rectangle([bx0, by0, bx1, by1], radius=28, fill=(255, 253, 247), outline=GOLD, width=2)
    draw_center(d, cx, by0 + 38, "あなたの月タイプは？", font(F_HANA, 64), NAVY)
    draw_center(d, cx, by0 + 138, "moonlog.jp で無料診断", font(F_GOTHIC, 50), GOLD)
    draw_center(d, cx, by0 + 205, "生年月日だけ ／ 1分 ／ 登録不要", font(F_GOTHIC, 34), GRAY)

    out = os.path.join(OUT_DIR, f"{key}.png")
    img.save(out)
    return out


def main():
    keys = [sys.argv[1]] if len(sys.argv) > 1 else list(TYPE_DATA.keys())
    for k in keys:
        p = build(k)
        print("✅", k, "→", os.path.relpath(p, ROOT))


if __name__ == "__main__":
    main()

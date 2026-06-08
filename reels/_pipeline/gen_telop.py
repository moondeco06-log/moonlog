# -*- coding: utf-8 -*-
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os, sys, datetime

FONT = "/Users/mitsuinatsuki/Library/Fonts/花とちょうちょ.ttf"
W, H = 1080, 1920
OUT = "/tmp/daily_star_frames"
os.makedirs(OUT, exist_ok=True)

WHITE = (252, 252, 250, 255)
SHADOW = (8, 10, 24)  # 濃紺の影

def draw_text(img, text, size, cy, fill=WHITE):
    """白文字＋やわらかい影。複数行対応。cy=行ブロックの中心Y"""
    font = ImageFont.truetype(FONT, size)
    lines = text.split("\n")
    asc, desc = font.getmetrics()
    lh = asc + desc + 24
    total = lh * len(lines)
    y0 = cy - total // 2

    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    y = y0
    for ln in lines:
        bbox = sd.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 - bbox[0]
        sd.text((x, y), ln, font=font, fill=(*SHADOW, 220))
        y += lh
    sh = sh.filter(ImageFilter.GaussianBlur(9))
    img.alpha_composite(sh)
    sh2 = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    s2 = ImageDraw.Draw(sh2)
    y = y0
    for ln in lines:
        bbox = s2.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 - bbox[0]
        s2.text((x + 2, y + 3), ln, font=font, fill=(*SHADOW, 180))
        y += lh
    sh2 = sh2.filter(ImageFilter.GaussianBlur(2))
    img.alpha_composite(sh2)
    d = ImageDraw.Draw(img)
    y = y0
    for ln in lines:
        bbox = d.textbbox((0, 0), ln, font=font)
        tw = bbox[2] - bbox[0]
        x = (W - tw) // 2 - bbox[0]
        d.text((x, y), ln, font=font, fill=fill)
        y += lh
    return img

# 日付（引数 YYYY-MM-DD があればその日、なければ今日）。タイトルの月日に反映。
today = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
date_jp = f"{today.month}月{today.day}日"
title = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_text(title, date_jp, 64, 235)
draw_text(title, "月のメッセージ", 86, 365)
title.save(f"{OUT}/title.png")

# 日替わりテロップ（主役＝その夜22時東京の月の星座）。固定：5枚目=キャプション誘導／7-9=訴求・CTA・締め
SCENES = {
    # 6/8 月＝魚座のおわり（感じきる・手放す・区切り）。月曜＝力を抜いて始める
    "2026-06-08": [
        ("手放すと\n軽くなる日", 116),
        ("月は魚座のおわり\n区切りのとき", 100),
        ("重く感じるものは\nおろしていい", 100),
        ("がんばった自分を\nねぎらう日", 100),
        ("涙が出る日も\nあっていい", 104),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
    # 6/9 月＝牡羊座へIN（始まり・行動・勇気）。火曜＝新しい一歩
    "2026-06-09": [
        ("新しい一歩を\nふみ出す日", 112),
        ("月は牡羊座へ\n始まりのエネルギー", 92),
        ("やりたいほうへ\n動いていい", 100),
        ("小さく始めて\nいい", 116),
        ("うまくなくても\n一歩は一歩", 104),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
    # 6/10 月＝牡羊座（勇気・自分から動く・情熱）。水曜
    "2026-06-10": [
        ("やりたいことから\n動く日", 100),
        ("月は牡羊座\n勇気がわく日", 104),
        ("迷うより\nまず一歩", 116),
        ("自分のやりたいを\n優先していい", 96),
        ("失敗しても\nやり直せる", 104),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
    # 6/11 月＝牡牛座IN（地に足・落ち着く・安定）。木曜
    "2026-06-11": [
        ("地に足を\nつける日", 112),
        ("月は牡牛座へ\n落ち着くとき", 100),
        ("あわてず\nゆっくりでいい", 104),
        ("立ち止まって\n味わっていい", 100),
        ("あなたのペースで\n進めばいい", 100),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
    # 6/12 月＝牡牛座（五感・心地よさ・豊かさ）。金曜
    "2026-06-12": [
        ("心地よさを\n選ぶ日", 112),
        ("月は牡牛座\n五感がよろこぶ日", 92),
        ("好きなものに\nふれてみる", 100),
        ("自分を\n甘やかしていい", 108),
        ("快適さは\nわがままじゃない", 92),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
    # 6/13 月＝牡牛座のおわり（整える・土台・確かめる）。土曜
    "2026-06-13": [
        ("大切なものを\n確かめる日", 100),
        ("月は牡牛座のおわり\n足場を整えるとき", 84),
        ("身のまわりを\nひとつ整える", 100),
        ("ゆっくり休む\n時間をとっていい", 90),
        ("土台があるから\nまた動ける", 100),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
    # 6/14 月＝双子座（好奇心・会話・軽やか）。日曜
    "2026-06-14": [
        ("軽やかに\n動ける日", 112),
        ("月は双子座\n好奇心がひらく日", 92),
        ("気になることを\n調べてみる", 96),
        ("あれこれ\n寄り道していい", 100),
        ("おしゃべりが\n心をほぐす", 100),
        ("星座のひとことは\nキャプションに", 104),
        ("moonlog", 140),
    ],
}
scenes = SCENES.get(today.isoformat())
if scenes is None:
    print("⚠️ この日付のテロップ内容(SCENES)が未定義です:", today.isoformat()); sys.exit(1)

CY = 1010
for i, (t, s) in enumerate(scenes):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_text(img, t, s, CY)
    img.save(f"{OUT}/scene{i}.png")

print("date:", date_jp, "| frames:", len(scenes), "+ title")

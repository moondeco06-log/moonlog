# -*- coding: utf-8 -*-
"""本音リール2本目「わたしを通す」＝夏紀さんの声入り版ビルダー。
声(DJI_21)の無音解析から字幕ブロックを声にシンクさせる。
使い方: python3 reels/_pipeline/build_honne2.py
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

ROOT = "/Users/mitsuinatsuki/Documents/AI_uranai"
FF = "/Users/mitsuinatsuki/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
BG = f"{ROOT}/reels/backgrounds/_miyako_honne.mp4"
VOICE = f"{ROOT}/reels/音声/DJI_21_20260706_083455.WAV"
BGM = os.path.expanduser("~/Documents/ongaku/releases/vol3/Vol3-02 Free as the Wave.mp3")
OUT = f"{ROOT}/reels/honne_02_toosu.mp4"
FR = "/tmp/honne2_frames"; os.makedirs(FR, exist_ok=True)

FONT = "/Users/mitsuinatsuki/Library/Fonts/花とちょうちょ.ttf"
W, H = 1080, 1920
WHITE = (252, 252, 250, 255); SHADOW = (8, 10, 24)
SIZE, CY = 86, 940

# --- 声のタイムライン ---
# 元WAV: 発話 2.48s〜31.07s（以降は物音）。頭を1.2sに合わせて全体を -1.28s シフト。
V_TRIM_IN, V_TRIM_OUT, V_DELAY = 1.28, 31.40, 0.0   # atrim 1.28-31.40 → 動画の1.28-31.40がそのまま0基点、adelayなしで開始2.48-1.28=1.20s
DUR = 34.8
# 字幕ブロック（動画時間・秒）＝発話セグメント(元時間-1.28)に対応
BLOCKS = [
    ("ずっと「私ばっかり」って\nイライラしてた",              1.00, 5.33),
    ("せっかちで、要領もよくて\nまわりに、つい苛立ってた",      5.33, 10.67),
    ("こんなにイライラしてる人生\nもったいない\nもっと、楽しく過ごしたい", 10.67, 17.14),
    ("でも、すぐには変われなくて\n心が疲れて、少し休んで\nやっと、わかった", 17.14, 24.96),
    ("他人に、なんと思われてもいい\n\nわたしは、わたしを通す",  24.96, 30.40),
]
LOGO = ("moonlog", 30.80, DUR)


def draw_text(img, text, size, cy, fill=WHITE):
    font = ImageFont.truetype(FONT, size)
    lines = text.split("\n")
    asc, desc = font.getmetrics(); lh = asc + desc + 24
    total = lh * len(lines); y0 = cy - total // 2
    for blur, dx, dy, a in ((9, 0, 0, 220), (2, 2, 3, 180)):
        sh = Image.new("RGBA", (W, H), (0, 0, 0, 0)); sd = ImageDraw.Draw(sh); y = y0
        for ln in lines:
            bb = sd.textbbox((0, 0), ln, font=font)
            sd.text(((W - (bb[2]-bb[0]))//2 - bb[0] + dx, y + dy), ln, font=font, fill=(*SHADOW, a))
            y += lh
        img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(blur)))
    d = ImageDraw.Draw(img); y = y0
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=font)
        d.text(((W - (bb[2]-bb[0]))//2 - bb[0], y), ln, font=font, fill=fill)
        y += lh
    return img


def make_scrim():  # 薄ヴェール（build_honne と同じ）
    NAVY = (10, 14, 30); MAX_A = 70
    col = np.zeros((H, 4), dtype=np.float32)
    def ramp(y, top, p0, p1, bot):
        if y < top or y > bot: return 0.0
        if y < p0: return (y - top) / (p0 - top)
        if y > p1: return (bot - y) / (bot - p1)
        return 1.0
    for y in range(H):
        a = ramp(y, 560, 720, 1240, 1380) * MAX_A
        col[y] = (*NAVY, a)
    arr = np.repeat(col[:, None, :], W, axis=1).astype(np.uint8)
    Image.fromarray(arr, "RGBA").filter(ImageFilter.GaussianBlur(30)).save(f"{FR}/scrim.png")


make_scrim()
for i, (txt, a, b) in enumerate(BLOCKS):
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_text(img, txt, SIZE, CY)
    img.save(f"{FR}/b{i}.png")
img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
draw_text(img, "moonlog", 140, 940)
img.save(f"{FR}/logo.png")

# ブーメラン背景（18.57s→往復37s）
boom = f"{FR}/boom.mp4"
if not os.path.exists(boom):
    subprocess.run([FF, "-y", "-i", BG, "-filter_complex",
        "[0:v]split[f][r];[r]reverse[rv];[f][rv]concat=n=2:v=1[v]",
        "-map", "[v]", "-t", str(DUR), "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20", boom], check=True)

# 合成：背景 + scrim + 字幕(声シンク) + ロゴ / 音声：声(loudnorm) + BGM(小さく)
inputs = [FF, "-y", "-i", boom, "-i", f"{FR}/scrim.png"]
for i in range(len(BLOCKS)):
    inputs += ["-i", f"{FR}/b{i}.png"]
inputs += ["-i", f"{FR}/logo.png", "-i", VOICE, "-ss", "72", "-i", BGM]
nb = len(BLOCKS)
vi_scrim, vi_first_block, vi_logo = 1, 2, 2 + nb
ai_voice, ai_bgm = 3 + nb, 4 + nb

fc = f"[0:v][{vi_scrim}:v]overlay=0:0[v0];"
cur = "v0"
for i, (txt, a, b) in enumerate(BLOCKS):
    fc += f"[{cur}][{vi_first_block+i}:v]overlay=0:0:enable='between(t,{a},{b})'[v{i+1}];"
    cur = f"v{i+1}"
la, lb = LOGO[1], LOGO[2]
fc += f"[{cur}][{vi_logo}:v]overlay=0:0:enable='between(t,{la},{lb})',fade=t=out:st={DUR-0.8}:d=0.8[vout];"
fc += (f"[{ai_voice}:a]atrim={V_TRIM_IN}:{V_TRIM_OUT},asetpts=PTS-STARTPTS,"
       f"loudnorm=I=-16:TP=-1.5:LRA=11,afade=t=out:st={V_TRIM_OUT-V_TRIM_IN-0.4}:d=0.4[vo];"
       f"[{ai_bgm}:a]atrim=0:{DUR},asetpts=PTS-STARTPTS,volume=0.13,"
       f"afade=t=in:st=0:d=1.5,afade=t=out:st={DUR-2.5}:d=2.5[bg];"
       f"[vo][bg]amix=inputs=2:duration=longest:normalize=0[aout]")
cmd = inputs + ["-filter_complex", fc, "-map", "[vout]", "-map", "[aout]",
    "-t", str(DUR), "-c:v", "libx264", "-preset", "fast", "-crf", "19",
    "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", OUT]
subprocess.run(cmd, check=True)
print("✅ 完成:", OUT)

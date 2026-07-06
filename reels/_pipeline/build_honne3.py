# -*- coding: utf-8 -*-
"""本音リール3本目「サイズ表」＝夏紀さんの声＋ミシン映像。
声(DJI_22)の無音解析＋whisper文字起こしから字幕を声にシンク。
使い方: python3 reels/_pipeline/build_honne3.py
"""
import os, subprocess
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import numpy as np

ROOT = "/Users/mitsuinatsuki/Documents/AI_uranai"
FF = "/Users/mitsuinatsuki/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
BG_SRC = "/Users/mitsuinatsuki/Documents/MIDORI_claude/DOUGA/ミシン1.MP4"
VOICE = f"{ROOT}/reels/音声/DJI_22_20260706_083537.WAV"
BGM = os.path.expanduser("~/Documents/ongaku/releases/vol3/Vol3-02 Free as the Wave.mp3")
OUT = f"{ROOT}/reels/honne_03_size.mp4"
FR = "/tmp/honne3_frames"; os.makedirs(FR, exist_ok=True)

FONT = "/Users/mitsuinatsuki/Library/Fonts/花とちょうちょ.ttf"
W, H = 1080, 1920
WHITE = (252, 252, 250, 255); SHADOW = (8, 10, 24)
SIZE, CY = 86, 940

# --- 声のタイムライン ---
# 元WAV: 発話 2.48s〜31.07s（以降は物音）。頭を1.2sに合わせて全体を -1.28s シフト。
V_TRIM_IN, V_TRIM_OUT, V_DELAY = 0.73, 35.90, 0.0   # 発話1.93s〜35.44s → 頭1.2sに合わせ全体-0.73s
DUR = 38.9
# 字幕ブロック（動画時間・秒）＝発話セグメント(元時間-1.28)に対応
BLOCKS = [
    ("多少太ってても、気にしない\n服は、自分で型紙から作るから",   1.00, 7.65),
    ("LとかMとか\nサイズ表に合わせなくていい\n自分の体に、合わせればいい", 7.65, 17.62),
    ("他人の評価も、他人の目も\nおなじ",                        17.62, 22.67),
    ("だいたい、自分を正確に\n把握してくれてる人なんて\nいない",   22.67, 28.56),
    ("だったら\n一般的なサイズ表じゃなくて\n\n自分に合わせて、生きればいい", 28.56, 35.30),
]
LOGO = ("moonlog", 35.70, DUR)


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
    NAVY = (10, 14, 30); MAX_A = 115
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

# 横1920x1080 → 縦1080x1920 切り出し（針もとが中心に来るよう x=1593）
boom = f"{FR}/bg_v.mp4"
if not os.path.exists(boom):
    subprocess.run([FF, "-y", "-ss", "3", "-t", str(DUR), "-i", BG_SRC,
        "-vf", "scale=-2:1920,crop=1080:1920:1593:0,fps=30",
        "-an", "-c:v", "libx264", "-preset", "fast", "-crf", "20", "-pix_fmt", "yuv420p", boom], check=True)

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

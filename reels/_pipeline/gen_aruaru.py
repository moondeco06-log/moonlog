# -*- coding: utf-8 -*-
"""「12タイプあるある」リール 専用ビルダー（毎朝の月メッセージとは別系統・試作）。
特徴：文字を大きく中央／1枚2.5秒のテンポ／最後に動物カード＋診断誘導。
使い方: python3 reels/_pipeline/gen_aruaru.py gemini   （typeキー＝星座英略）
"""
import os, sys, glob, subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT = "/Users/mitsuinatsuki/Documents/code_yousai"
FF = "/Users/mitsuinatsuki/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
FONT = "/Users/mitsuinatsuki/Library/Fonts/花とちょうちょ.ttf"
FR = "/tmp/aruaru_frames"
os.makedirs(FR, exist_ok=True)
W, H = 1080, 1920
# クリーム無地＋金フレーム背景。文字は濃紺＋ごく薄い影でくっきり（雑誌風）
INK = (30, 40, 74, 255)       # 濃紺の本文
SHADOW = (120, 100, 70)       # 温かいグレーの薄い影（クリームから上品に浮かす）
GOLD = (140, 104, 28, 255)    # 濃いめゴールド（カードのネタバラシ用）
WHITE = INK                   # draw_text既定をINKに

# ── タイプ別あるある（試作はリス＝双子座の月。夏紀さん監修）──
ARUARU = {
    "gemini": {
        "sign": "双子座の月", "animal": "リス", "img": "gemini.png",
        "frames": [
            ("気づくと\nタブが20個\n開いてる", 128),          # フック
            ("動画は\nだいたい2倍速", 132),                    # あるある①
            ("何かしながら\nいつも別のことも\nしてる", 116),    # あるある②（ながら）
            ("一気にハマって\n3日で\n次の興味へ", 122),        # あるある③（核心）
            ("__CARD__", 0),                                   # ネタバラシ（カード）
            ("あなたは\n何タイプ？\n\nプロフィールから\n30秒で診断", 110),  # 誘導
        ],
        "caption": """「集中力がない」って、ずっと言われてきた

でもそれ、欠点じゃなくて——
いろんなことに同時に光を当てられる
双子座の月の才能かも

あなたの"素の自分"は、何タイプ？
▶ 生年月日だけ・30秒・無料で診断（プロフィールのリンクから）

#月星座 #双子座 #自己理解 #moonlog #星占い #あるある #性格診断""",
    },
}

NF = 6
PER = 2.5
DUR = NF * PER          # 15.0秒
FADE_IN = 0.08          # ポンッと速く出す（唐突さ＝無音フェード対策）
FADE_OUT = 0.18
windows = [(i*PER, (i+1)*PER) for i in range(NF)]


def draw_text(img, text, size, cy, fill=WHITE):
    font = ImageFont.truetype(FONT, size)
    lines = text.split("\n")
    asc, desc = font.getmetrics()
    lh = asc + desc + 20
    total = lh * len(lines)
    y0 = cy - total // 2
    # ごく薄い影（クリームから上品に浮かす・1回・小ブラー）
    sh = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    sd = ImageDraw.Draw(sh)
    y = y0
    for ln in lines:
        bb = sd.textbbox((0, 0), ln, font=font); tw = bb[2]-bb[0]
        sd.text(((W-tw)//2 - bb[0]+2, y+3), ln, font=font, fill=(*SHADOW, 110)); y += lh
    img.alpha_composite(sh.filter(ImageFilter.GaussianBlur(5)))
    # 本体
    d = ImageDraw.Draw(img); y = y0
    for ln in lines:
        bb = d.textbbox((0, 0), ln, font=font); tw = bb[2]-bb[0]
        d.text(((W-tw)//2 - bb[0], y), ln, font=font, fill=fill); y += lh


def card_frame(data):
    """動物カード＋ネタバラシ文を1枚に。"""
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    card = Image.open(os.path.join(ROOT, "static/images/types/final", data["img"])).convert("RGBA")
    cs = 560
    card = card.resize((cs, cs), Image.LANCZOS)
    img.alpha_composite(card, ((W-cs)//2, 470))
    draw_text(img, f"これ {data['sign']}\n「{data['animal']}」タイプ", 92, 1180, fill=GOLD)
    draw_text(img, "いろんなことに\n同時に光を当てる才能", 78, 1420)
    return img


def make_scrim():
    # ポップ背景は明るいのでヴェール不要（白ハロで文字を浮かせる）。透明1枚を置く。
    Image.new("RGBA", (W, H), (0, 0, 0, 0)).save(f"{FR}/scrim.png")


def gen_frames(data):
    for f in glob.glob(f"{FR}/scene*.png"): os.remove(f)
    for i, (txt, size) in enumerate(data["frames"]):
        img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        if txt == "__CARD__":
            img = card_frame(data)
        else:
            draw_text(img, txt, size, 960)
        img.save(f"{FR}/scene{i}.png")
    make_scrim()


def pick_bg():
    # あるある専用のポップ背景（クリーム＋ドット・夜空でなく明るい世界）
    return os.path.join(ROOT, "reels/backgrounds_aruaru_pop.mp4")


def build(data):
    gen_frames(data)
    bg = pick_bg()
    boom = "/tmp/aruaru_bg.mp4"
    subprocess.run([FF,"-y","-i",bg,"-an","-vf",
                    "scale=1080:1920,fps=30,setpts=PTS-STARTPTS","-t",str(DUR+0.4),boom],
                   capture_output=True, text=True)
    inputs = ["-i",boom,"-loop","1","-t",str(DUR),"-i",f"{FR}/scrim.png"]
    for i in range(NF):
        inputs += ["-loop","1","-t",str(DUR),"-i",f"{FR}/scene{i}.png"]
    fc = [f"[0:v]scale=1080:1920,fps=30,trim=0:{DUR},setpts=PTS-STARTPTS[bgraw]",
          "[bgraw][1:v]overlay=0:0[b0]"]
    prev = "b0"
    # 各テキストを一瞬で拡大しながら出す（pop-in：0.9→1.0）＋速いフェード
    for i,(s,e) in enumerate(windows):
        inp = i+2; d = e-s
        fc.append(f"[{inp}:v]format=rgba,"
                  f"scale=w='iw*min(1,0.9+0.1*min(1,(t)/0.18))':h=-1:eval=frame,"
                  f"fade=t=in:st=0:d={FADE_IN}:alpha=1,"
                  f"fade=t=out:st={d-FADE_OUT:.3f}:d={FADE_OUT}:alpha=1,"
                  f"setpts=PTS-STARTPTS+{s}/TB[s{i}]")
        fc.append(f"[{prev}][s{i}]overlay=(W-w)/2:(H-h)/2:enable='between(t,{s},{e})'[v{i}]")
        prev = f"v{i}"
    fc.append(f"[{prev}]fade=t=out:st={DUR-0.5}:d=0.5:color=black[outv]")
    silent = "/tmp/aruaru_silent.mp4"
    cmd = [FF,"-y",*inputs,"-filter_complex",";".join(fc),"-map","[outv]",
           "-t",str(DUR),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",
           "-profile:v","high","-crf","20","-an",silent]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:\n", r.stderr[-2000:]); sys.exit(1)
    # BGM＝ありがとうデイリー vol21（明るいライン・朝カフェ系）。イントロ飛ばして15秒。
    bgm = os.path.expanduser("~/Documents/ongaku/releases/vol21/07 Walking with a Smile.mp3")
    out = os.path.join(ROOT, f"reels/aruaru_{data['img'].replace('.png','')}.mp4")
    r = subprocess.run([FF,"-y","-i",silent,"-ss","18","-i",bgm,
        "-filter_complex",
        "[1:a]atrim=0:%s,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.0,"
        "afade=t=out:st=%.1f:d=1.8,volume=0.85[a]" % (DUR, DUR-1.8),
        "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",out],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("BGM STDERR:\n", r.stderr[-1500:]); sys.exit(1)
    print(f"✅ 完成: {out}  ({DUR}秒 / {NF}枚 / 背景 {os.path.basename(bg)})")
    # キャプション保存
    cap_path = os.path.join(ROOT, f"instagram_posts/aruaru_{data['img'].replace('.png','')}_caption.txt")
    open(cap_path, "w", encoding="utf-8").write(data["caption"])
    print(f"   キャプション: {cap_path}")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else "gemini"
    build(ARUARU[key])

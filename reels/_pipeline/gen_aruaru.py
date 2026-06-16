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

# ── タイプ別あるある（12タイプ・夏紀さん監修済み 2026-06-16）──
# あるある監修3原則は memory/feedback_aruaru_copy_rules.md 参照
# （①具体的すぎ/人による はNG ②自分で気づけないこと はNG ③カードは抽象名詞でまとめない）
# 下書き・編集元は drafts/aruaru_drafts_11types.md
_CTA = "あなたは\n何タイプ？\n\nプロフィールから\n30秒で診断"


def _caption(line1, reframe_phrase, sign_jp):
    return (f"{line1}\n\n"
            f"でもそれ、欠点じゃなくて——\n{reframe_phrase}\n{sign_jp}の月の才能かも\n\n"
            f"あなたの\"素の自分\"は、何タイプ？\n"
            f"▶ 生年月日だけ・30秒・無料で診断（プロフィールのリンクから）\n\n"
            f"#月星座 #{sign_jp} #自己理解 #moonlog #星占い #あるある #性格診断")


ARUARU = {
    "gemini": {
        "sign": "双子座の月", "animal": "リス", "img": "gemini.png",
        "reframe": "いろんなことに\n同時に光を当てる才能",
        "frames": [
            ("気づくと\nタブが20個\n開いてる", 128),
            ("動画は\nだいたい2倍速", 132),
            ("何かしながら\nいつも別のことも\nしてる", 116),
            ("一気にハマって\n3日で\n次の興味へ", 122),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「集中力がない」って、ずっと言われてきた",
                            "いろんなことに同時に光を当てられる", "双子座"),
    },
    "aries": {
        "sign": "牡羊座の月", "animal": "柴犬", "img": "aries.png",
        "reframe": "誰より早く\n動ける行動力",
        "frames": [
            ("思いついたら\nもう動いてる", 126),
            ("「とりあえず\nやってみる」が\n口ぐせ", 114),
            ("列に並ぶのが\n世界一苦手", 122),
            ("カッとなるけど\n5分後には\nケロッ", 116),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「せっかちだね」って、ずっと言われてきた",
                            "誰より早く動ける", "牡羊座"),
    },
    "taurus": {
        "sign": "牡牛座の月", "animal": "アルパカ", "img": "taurus.png",
        "reframe": "一度決めたら\nブレない人",
        "frames": [
            ("急かされると\nかたまって\n動けない", 116),
            ("お気に入りは\nずっと同じものを\n使う", 112),
            ("「ちょっと待って」が\n本当に\nちょっとじゃない", 100),
            ("決めるのは遅いけど\n決めたら\n揺るがない", 104),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「のんびりしすぎ」って、ずっと言われてきた",
                            "一度決めたらブレない", "牡牛座"),
    },
    "cancer": {
        "sign": "蟹座の月", "animal": "うさぎ", "img": "cancer.png",
        "reframe": "帰る場所を\nつくれる優しさ",
        "frames": [
            ("人の機嫌に\nすぐ気づいちゃう", 120),
            ("人のことだと\n自分以上に\n本気になる", 116),
            ("友だちの相談で\n気づけば\n自分が泣いてる", 106),
            ("「大丈夫?」が\n口ぐせ", 126),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「気にしすぎ」って、ずっと言われてきた",
                            "人の気持ちに気づける", "蟹座"),
    },
    "leo": {
        "sign": "獅子座の月", "animal": "ライオン", "img": "leo.png",
        "reframe": "まわりを\n照らす明るさ",
        "frames": [
            ("ほめられると\n3割増しで\nがんばれる", 116),
            ("リアクションが\nつい大きい", 120),
            ("うれしいと\n顔に出ちゃう", 124),
            ("主役じゃなくても\n空気は\n明るくしたい", 110),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「目立ちたがり」って、ずっと言われてきた",
                            "まわりを明るくできる", "獅子座"),
    },
    "virgo": {
        "sign": "乙女座の月", "animal": "はりねずみ", "img": "virgo.png",
        "reframe": "小さな変化に\nすぐ気づく人",
        "frames": [
            ("気になると\n直さずに\nいられない", 118),
            ("予定は細かく\n立てたい", 122),
            ("「まだ足りない」が\n口ぐせ", 110),
            ("人の役に立つと\nやっと\nほっとする", 114),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「神経質」って、ずっと言われてきた",
                            "小さな変化に気づける", "乙女座"),
    },
    "libra": {
        "sign": "天秤座の月", "animal": "白鳥", "img": "libra.png",
        "reframe": "その場の空気を\nなごませる人",
        "frames": [
            ("「どっちでもいいよ」\nが口ぐせ", 102),
            ("険悪な空気が\n何より苦手", 120),
            ("人によって\n少しずつ\nキャラが変わる", 112),
            ("自分の意見は\nつい後回し", 120),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「優柔不断」って、ずっと言われてきた",
                            "みんなの心地よさを考えられる", "天秤座"),
    },
    "scorpio": {
        "sign": "蠍座の月", "animal": "オオカミ", "img": "scorpio.png",
        "reframe": "深く愛せる\n情熱",
        "frames": [
            ("好きになると\nとことん深く", 120),
            ("広く浅くが\nできない", 124),
            ("本音はなかなか\n見せない", 120),
            ("一度の裏切りは\nずっと忘れない", 114),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「重い」って、ずっと言われてきた",
                            "ひとつを深く愛せる", "蠍座"),
    },
    "sagittarius": {
        "sign": "射手座の月", "animal": "ウマ", "img": "sagittarius.png",
        "reframe": "いつも\n前を向ける明るさ",
        "frames": [
            ("縛られると\n逃げたくなる", 122),
            ("「なんとかなる」が\n口ぐせ", 110),
            ("計画より\nノリで決めがち", 120),
            ("終わってないのに\nもう次が\n気になる", 110),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「飽きっぽい」って、ずっと言われてきた",
                            "いつも前を向ける", "射手座"),
    },
    "capricorn": {
        "sign": "山羊座の月", "animal": "ヤギ", "img": "capricorn.png",
        "reframe": "こつこつ\n積みあげる力",
        "frames": [
            ("遊ぶ前に\n「やること」を\n片づけたい", 112),
            ("目標がないと\n落ち着かない", 118),
            ("弱音はなかなか\n吐けない", 118),
            ("休むのが\nじつは苦手", 124),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「真面目すぎ」って、ずっと言われてきた",
                            "こつこつ本物を積みあげる", "山羊座"),
    },
    "aquarius": {
        "sign": "水瓶座の月", "animal": "ふくろう", "img": "aquarius.png",
        "reframe": "流されずに\n自分を貫ける人",
        "frames": [
            ("みんなと同じが\nちょっと苦手", 116),
            ("流行より\n自分の「好き」", 120),
            ("熱くなる前に\n一歩引いて\n見ちゃう", 112),
            ("「変わってるね」は\nほめ言葉", 110),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「マイペース」って、ずっと言われてきた",
                            "自分の軸で生きられる", "水瓶座"),
    },
    "pisces": {
        "sign": "魚座の月", "animal": "シカ", "img": "pisces.png",
        "reframe": "人の気持ちが\n分かりすぎる人",
        "frames": [
            ("人の感情を\nもらって疲れる", 118),
            ("映画で\nすぐ泣く", 128),
            ("気づけば\n空想の世界へ", 122),
            ("「ノー」が\nなかなか言えない", 116),
            ("__CARD__", 0),
            (_CTA, 110),
        ],
        "caption": _caption("「繊細すぎ」って、ずっと言われてきた",
                            "人の気持ちに寄りそえる", "魚座"),
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
    draw_text(img, data["reframe"], 78, 1420)
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

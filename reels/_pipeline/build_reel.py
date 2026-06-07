# -*- coding: utf-8 -*-
"""毎朝の「月のメッセージ」リールを組み立てる（背景ローテ＋BGM焼込みまで全自動）。
使い方:
  1) reels/_pipeline/gen_telop.py の scenes と タイトルを今日の内容に編集して実行
     （/tmp/daily_star_frames に title.png / scene0..8.png ができる）
  2) python3 reels/_pipeline/build_reel.py [YYYY-MM-DD]
     → reels/daily_<日付>_BGM.mp4 が完成（BGM・無音版どちらも出力）

背景:
  reels/backgrounds/ に .mp4 を置くと日付で自動ローテーション（曜日違いの絵になる）。
  まだ無い/不足なら reels/リール元画像canva.mp4 にフォールバック。
BGM:
  夏紀さん自身の Slow Hours（インスト・著作権クリア）を日付でローテーション。
"""
import os, sys, glob, subprocess, datetime

ROOT = "/Users/mitsuinatsuki/Documents/code_yousai"
FF = "/Users/mitsuinatsuki/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
FR = "/tmp/daily_star_frames"
BG_DIR = os.path.join(ROOT, "reels", "backgrounds")
BG_FALLBACK = os.path.join(ROOT, "reels", "リール元画像canva.mp4")
BOOM = "/tmp/bg_boomerang.mp4"

# BGM候補（夏紀さん Slow Hours・インスト・夜に合う順）
BGM_POOL = [
    "slow_hours/vol4_okinawa_sunset/08_twilight_ballad_rhodes.mp3",
    "slow_hours/vol4_okinawa_sunset/09_lighthouse_glow_rhodes.mp3",
    "slow_hours/vol5_kamakura_beach/V5_08 Quiet Cove Rhodes.mp3",
    "slow_hours/vol4_okinawa_sunset/07_tide_pool_wurli.mp3",
    "slow_hours/vol5_kamakura_beach/V5_07 Open Window Wurlitzer.mp3",
    "slow_hours/vol4_okinawa_sunset/06_golden_hour_wurlitzer.mp3",
    "slow_hours/vol5_kamakura_beach/V5_06 Harbor Light Wurlitzer.mp3",
]
ONGAKU = os.path.expanduser("~/Documents/ongaku")

DUR = 20.3
FADE = 0.22
# 7シーン構成（フック/今日の星/行動/許可/後押し/キャプション誘導/moonlog）
windows = [(0.0,2.9),(2.9,5.8),(5.8,8.7),(8.7,11.5),(11.5,14.3),
           (14.3,17.2),(17.2,20.3)]
N_SCENES = 7


def pick_by_date(items, date):
    if not items:
        return None
    return items[date.toordinal() % len(items)]


def make_boomerang(src):
    """背景は normalize_bg.py で 1080x1920 / 30fps / 約21秒 に正規化済み。
    ここでは頭からDUR分そろえるだけ（暗い冒頭スキップ・引き伸ばしは正規化側で完了）。"""
    subprocess.run([FF,"-y","-i",src,"-an","-vf",
                    "scale=1080:1920,fps=30,setpts=PTS-STARTPTS","-t",str(DUR+0.4),BOOM],
                   capture_output=True, text=True)


def make_scrim():
    """どの背景でも文字が読めるよう、タイトル帯と本文帯にだけ薄暗いヴェールを敷く。
    背景全体は暗くせず、文字位置だけ柔らかく落とす（背景の雰囲気は保つ）。"""
    from PIL import Image, ImageDraw, ImageFilter
    sc = Image.new("RGBA", (1080, 1920), (0, 0, 0, 0))
    d = ImageDraw.Draw(sc)
    # タイトル帯（上部 y~180-430）
    d.rounded_rectangle([90, 150, 990, 470], radius=200, fill=(10, 14, 30, 120))
    # 本文帯（中央やや下 y~800-1230／CY=1010中心）
    d.rounded_rectangle([40, 770, 1040, 1260], radius=260, fill=(10, 14, 30, 135))
    sc = sc.filter(ImageFilter.GaussianBlur(70))
    sc.save(f"{FR}/scrim.png")


def build_silent(out):
    make_scrim()
    inputs = ["-i",BOOM,
              "-loop","1","-t",str(DUR),"-i",f"{FR}/scrim.png",
              "-loop","1","-t",str(DUR),"-i",f"{FR}/title.png"]
    for i in range(N_SCENES):
        inputs += ["-loop","1","-t",str(DUR),"-i",f"{FR}/scene{i}.png"]
    fc = [f"[0:v]scale=1080:1920,fps=30,trim=0:{DUR},setpts=PTS-STARTPTS[bgraw]",
          "[bgraw][1:v]overlay=0:0[bg]",
          "[bg][2:v]overlay=0:0[b0]"]
    prev = "b0"
    for i,(s,e) in enumerate(windows):
        inp = i+3; d = e-s
        fc.append(f"[{inp}:v]format=rgba,fade=t=in:st=0:d={FADE}:alpha=1,"
                  f"fade=t=out:st={d-FADE:.3f}:d={FADE}:alpha=1,setpts=PTS-STARTPTS+{s}/TB[s{i}]")
        fc.append(f"[{prev}][s{i}]overlay=0:0:enable='between(t,{s},{e})'[v{i}]")
        prev = f"v{i}"
    # 最初と最後を黒からフェード（白い開幕・ループ継ぎ目の白フラッシュを消す）
    fc.append(f"[{prev}]fade=t=in:st=0:d=0.4:color=black,"
              f"fade=t=out:st={DUR-0.5}:d=0.5:color=black[outv]")
    prev = "outv"
    cmd = [FF,"-y",*inputs,"-filter_complex",";".join(fc),"-map",f"[{prev}]",
           "-t",str(DUR),"-c:v","libx264","-pix_fmt","yuv420p","-r","30",
           "-profile:v","high","-crf","20","-an",out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print("STDERR:\n", r.stderr[-2000:]); sys.exit(1)


def bake_bgm(silent, bgm, out):
    r = subprocess.run([FF,"-y","-i",silent,"-ss","12","-i",bgm,
        "-filter_complex",
        "[1:a]atrim=0:%s,asetpts=PTS-STARTPTS,afade=t=in:st=0:d=1.2,"
        "afade=t=out:st=%.1f:d=2.2,volume=0.85[a]" % (DUR, DUR-2.2),
        "-map","0:v","-map","[a]","-c:v","copy","-c:a","aac","-b:a","192k","-shortest",out],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("BGM STDERR:\n", r.stderr[-2000:]); sys.exit(1)


def main():
    date = datetime.date.fromisoformat(sys.argv[1]) if len(sys.argv) > 1 else datetime.date.today()
    ds = date.isoformat()
    # 背景選択
    bgs = sorted(glob.glob(os.path.join(BG_DIR, "*.mp4")))
    src = pick_by_date(bgs, date) or (BG_FALLBACK if os.path.exists(BG_FALLBACK) else None)
    if not src:
        print("背景動画がありません（backgrounds/ も canva も無し）"); sys.exit(1)
    print(f"背景: {os.path.basename(src)}  （候補{len(bgs)}枚）")
    make_boomerang(src)
    # 組み立て
    silent = os.path.join(ROOT, "reels", f"daily_{ds}.mp4")
    final = os.path.join(ROOT, "reels", f"daily_{ds}_BGM.mp4")
    build_silent(silent)
    bgm_rel = pick_by_date(BGM_POOL, date)
    bgm = os.path.join(ONGAKU, bgm_rel)
    print(f"BGM: {os.path.basename(bgm)}")
    bake_bgm(silent, bgm, final)
    print(f"\n✅ 完成: {final}")
    print(f"   投稿: python3 igpost.py reel {ds}")


if __name__ == "__main__":
    main()

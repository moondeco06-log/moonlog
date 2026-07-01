# -*- coding: utf-8 -*-
"""背景素材を「1080x1920 / 30fps / 約21秒 / mp4」に正規化してプールに揃える。
夏紀さん撮影の .MOV（尺バラバラ）と、残す既存背景を統一規格にする。
短い素材はスロー、長い素材は良い区間をトリム。出力は backgrounds/ 直下（build_reelのglobが拾う）。"""
import os, re, subprocess

BG = "/Users/mitsuinatsuki/Documents/AI_uranai/reels/backgrounds"
FF = "/Users/mitsuinatsuki/Library/Python/3.9/lib/python/site-packages/imageio_ffmpeg/binaries/ffmpeg-macos-aarch64-v7.1"
DUR_T = 21.0  # 正規化尺（build側DUR<これ。余裕を持たせる）

# (元ファイル, 開始秒=いい区間, 出力名)
SRC = [
    ("2.mp4",          0.9, "02.mp4"),   # 既存・夕暮れの海＋三日月（ブランドにベスト→残す）
    ("8_IMG_5863.MOV", 2.0, "08.mp4"),   # 畑と木
    ("9_IMG_5866.MOV", 3.0, "09.mp4"),   # カーテン越しの庭
    ("10_IMG_5884.MOV",2.0, "10.mp4"),   # ラベンダー畑
    ("11_IMG_5984.MOV",3.0, "11.mp4"),   # 庭の宿根草
    ("12_IMG_6216.MOV",3.0, "12.mp4"),   # 滝・苔
    ("13_IMG_6494.MOV",5.0, "13.mp4"),   # 機内から雲海・空
    ("14_IMG_6818.MOV",0.3, "14.mp4"),   # 並木の見上げ
]

def dur_of(path):
    info = subprocess.run([FF, "-i", path], capture_output=True, text=True).stderr
    m = re.search(r"Duration: (\d+):(\d+):(\d+\.\d+)", info)
    return 3600*int(m.group(1))+60*int(m.group(2))+float(m.group(3)) if m else 0.0

for src, start, out in SRC:
    sp = os.path.join(BG, src)
    if not os.path.exists(sp):
        print(f"⚠ 元ファイルなし: {src}"); continue
    d = dur_of(sp)
    avail = d - start
    tmp_out = os.path.join(BG, "_norm_" + out)
    if avail >= DUR_T:
        vf = "scale=1080:1920,fps=30,setpts=PTS-STARTPTS"
        mode = f"トリム(尺{d:.1f}s 開始{start}s)"
    else:
        factor = DUR_T / max(0.5, avail)
        vf = f"scale=1080:1920,fps=30,setpts=PTS*{factor:.4f}"
        mode = f"スロー×{factor:.2f}(尺{d:.1f}s 開始{start}s)"
    cmd = [FF, "-y", "-ss", f"{start}", "-i", sp, "-an", "-t", f"{DUR_T}",
           "-vf", vf, "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "20",
           "-profile:v", "high", "-r", "30", tmp_out]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        print(f"✗ {out} 失敗\n", r.stderr[-800:]); continue
    os.replace(tmp_out, os.path.join(BG, out))
    print(f"✓ {out}  {mode}")

print("\n正規化完了。backgrounds直下の 02/08-14.mp4 がプールになりました。")

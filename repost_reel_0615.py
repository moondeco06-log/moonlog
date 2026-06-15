"""6/15リールを新レイアウト（フック大・上配置・暗い帯強化）で出し直す。
旧投稿は夏紀さんが削除する前提。キャッシュ回避のため新URL(daily_2026-06-15-v2.mp4)で投稿。"""
import os, sys, time, json, shutil, subprocess, requests, datetime

ROOT = "/Users/mitsuinatsuki/Documents/code_yousai"
for line in open(os.path.join(ROOT, ".env")):
    line = line.strip()
    if line and not line.startswith("#") and "=" in line:
        k, v = line.split("=", 1); os.environ[k] = v
IG_BA = os.environ["IG_BUSINESS_ID"]; TOK = os.environ["FB_PAGE_TOKEN"]
os.chdir(ROOT)

vid = os.path.join(ROOT, "reels/daily_2026-06-15_BGM.mp4")
remote = "daily_2026-06-15-v2.mp4"
dest = os.path.join(ROOT, "static/videos/reels", remote)
url = f"https://moonlog.jp/static/videos/reels/{remote}"
cap = open(os.path.join(ROOT, "instagram_posts/daily_star_caption_2026-06-15.txt"), encoding="utf-8").read().strip()

shutil.copy(vid, dest)
subprocess.run(f'git add -f "{dest}"', shell=True)
subprocess.run('git commit -m "Repost 6/15 reel (new layout: bigger hook, higher, stronger scrim)" 2>&1 | tail -1', shell=True)
subprocess.run("git push origin main 2>&1 | tail -2", shell=True)

print("デプロイ待ち...", flush=True)
for i in range(40):
    time.sleep(8)
    code = subprocess.run(f'curl -s -o /dev/null -w "%{{http_code}}" {url}', shell=True, capture_output=True, text=True).stdout.strip()
    if code == "200":
        print(f"  デプロイ完了 {(i+1)*8}s", flush=True); break
    print(f"  待機 {(i+1)*8}s HTTP {code}", flush=True)
else:
    print("デプロイtimeout"); sys.exit(1)

print("REELSコンテナ作成...", flush=True)
r = requests.post(f"https://graph.facebook.com/v21.0/{IG_BA}/media",
                  data={"media_type": "REELS", "video_url": url, "caption": cap,
                        "thumb_offset": 1400, "access_token": TOK}, timeout=120).json()
if "id" not in r:
    print("コンテナerr", r); sys.exit(1)
cid = r["id"]; print("  container", cid, flush=True)

for i in range(30):
    time.sleep(10)
    s = requests.get(f"https://graph.facebook.com/v21.0/{cid}",
                     params={"fields": "status_code", "access_token": TOK}, timeout=60).json()
    print(f"  処理 {(i+1)*10}s {s.get('status_code')}", flush=True)
    if s.get("status_code") == "FINISHED": break
    if s.get("status_code") == "ERROR":
        print("処理err", s); sys.exit(1)
else:
    print("処理timeout"); sys.exit(1)

pr = requests.post(f"https://graph.facebook.com/v21.0/{IG_BA}/media_publish",
                   data={"creation_id": cid, "access_token": TOK}, timeout=120).json()
if "id" not in pr:
    print("公開err", pr); sys.exit(1)

st = json.load(open(os.path.join(ROOT, "instagram_posts/_state.json"), encoding="utf-8"))
st["reel:daily_2026-06-15.mp4"] = {"container_id": cid, "video_url": url, "published": True,
                                   "published_at": datetime.datetime.now().isoformat(), "post_id": pr["id"],
                                   "note": "新レイアウト・フック大/上/帯強化で出し直し"}
json.dump(st, open(os.path.join(ROOT, "instagram_posts/_state.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print(f"\n✅✅✅ 新レイアウトで出し直し完了！ 投稿ID: {pr['id']}", flush=True)

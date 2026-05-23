# -*- coding: utf-8 -*-
"""
星読みレポート Web アプリ
Flask で起動し、ブラウザからフォーム入力してHTMLまたはPPTXを生成します。
"""

import os, io, tempfile, warnings, threading
from dotenv import load_dotenv
load_dotenv()

CONTACT_EMAIL = os.environ.get("MOONLOG_EMAIL", "info@moonlog.jp")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
warnings.filterwarnings("ignore")

from flask import Flask, request, render_template_string, send_file, jsonify, redirect
from moonlog_astrology import generate_report, generate_html_report, resolve_location, generate_solar_return_html, generate_lifecycle_html
import moonlog_types
from moonlog_field_report import generate_field_report_html

app = Flask(__name__)

def _preload():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        fig, ax = plt.subplots(1, 1, figsize=(2, 2))
        plt.close(fig)
        from kerykeion import AstrologicalSubject
        s = AstrologicalSubject("_warm_", 2000, 1, 1, 12, 0,
                                lng=139.65, lat=35.68, tz_str="Asia/Tokyo")
        _ = s.sun
        from pptx import Presentation
        _ = Presentation()
        print("  ✅ プリロード完了")
    except Exception as e:
        print(f"  ⚠️  プリロード中のエラー: {e}")

threading.Thread(target=_preload, daemon=True).start()

# ============================================================
# HTML テンプレート
# ============================================================

HTML = """<!DOCTYPE html>
<html lang="ja">
<head>
  <!-- Google Analytics 4 -->
  <script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
  <script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){dataLayer.push(arguments);}
  gtag('js', new Date());
  gtag('config', 'G-KT19PT0DDG');
  </script>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>MOONLOG — 自分を知るための、静かな航海日誌</title>
  <meta name="robots" content="noindex, nofollow, noarchive, nosnippet, noimageindex">
  <meta name="googlebot" content="noindex, nofollow, noarchive">
  <meta name="CCBot" content="noindex">
  <meta name="GPTBot" content="noindex">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Noto+Serif+JP:wght@300;400;500;600&family=Noto+Sans+JP:wght@300;400;500&family=Cormorant+Garamond:ital,wght@0,300;0,400;1,300;1,400&family=Shippori+Mincho:wght@300;400;500;600&display=swap" rel="stylesheet">
  <style>
/* ─── CSS 変数（C案：和モダン・インディゴ） ─── */
:root {
  --base:       #F5F2EC;   /* 生成り（ベース）*/
  --base-warm:  #EEE8DC;   /* 温かみのあるクリーム（中間）*/
  --base-lav:   #EDE7DB;   /* 温かいアイボリー（中間・旧blue-gray→warm）*/
  --base-soft:  #F8F5F0;   /* やわらかいオフホワイト */
  --white:      #FFFFFF;
  --border:     #D8D0C4;   /* 温かみのあるベージュ枠線 */
  --border-l:   #E8E2D8;
  --gold:       #2C3E6B;   /* メインアクセント：インディゴブルー */
  --gold-l:     #4A5E8F;   /* 明るめインディゴ */
  --gold-d:     #1A2847;   /* 濃いインディゴ */
  --lav:        #7B90C4;   /* サブアクセント：ミディアムブルー */
  --lav-l:      #A4B5D8;   /* 薄いブルー */
  --lav-d:      #2C3E6B;   /* 濃いブルー（goldと同色） */
  --rose:       #8A9BB8;   /* くすみブルーグレー */
  --rose-l:     #B0BDD0;
  --text-d:     #2A2A2A;   /* ほぼ黒（メインテキスト）*/
  --text-m:     #555555;   /* ミディアムグレー */
  --text-l:     #888888;   /* 薄いグレー */
  --serif:      "Shippori Mincho", "Noto Serif JP", "Cormorant Garamond", serif;
  --sans:       "Noto Sans JP", sans-serif;
  --en:         "Cormorant Garamond", serif;
  /* 旧変数の互換 */
  --night: var(--base);
  --navy: var(--base-lav);
  --navy2: var(--base-warm);
  --navy3: var(--base-soft);
  --cream: var(--white);
  --cream2: var(--base-warm);
  --cream3: var(--border);
  --gold-ll: var(--gold-l);
}
*, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
html { scroll-behavior: smooth; }
body { font-family: var(--sans); font-weight: 300; color: var(--text-d); background: var(--base); }

/* ─── ナビゲーション ─── */
nav {
  position: fixed; top: 0; left: 0; right: 0; z-index: 200;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 3rem;
  height: 64px;
  background: rgba(250,246,238,0.85);
  backdrop-filter: blur(16px) saturate(1.2);
  border-bottom: 1px solid rgba(184,152,90,0.18);
}
.nav-logo {
  font-family: var(--serif);
  font-size: 0.95rem;
  font-weight: 400;
  color: var(--gold-d);
  text-decoration: none;
  letter-spacing: 0.2em;
}
.nav-links { display: flex; gap: 2.4rem; list-style: none; }
.nav-links a {
  font-size: 0.78rem;
  color: var(--text-m);
  text-decoration: none;
  letter-spacing: 0.1em;
  transition: color 0.25s;
}
.nav-links a:hover { color: var(--gold-d); }

/* ─── ヒーロー（明け方の空：藤色→生成り）─── */
#hero {
  min-height: 100vh;
  display: flex; flex-direction: column;
  align-items: center; justify-content: center;
  text-align: center;
  padding: 9rem 2rem 6rem;
  position: relative;
  overflow: hidden;
  background:
    linear-gradient(180deg, rgba(255,255,255,0) 0%, rgba(232,235,242,0.5) 70%, #E8EBF2 100%),
    url('/static/images/hero_top_light.png') center center / cover no-repeat;
}
/* 星粒 */
.starfield {
  position: absolute; inset: 0; pointer-events: none; overflow: hidden;
}
.starfield::before {
  content: "";
  position: absolute; inset: 0;
  background-image:
    radial-gradient(1.2px 1.2px at  8% 12%, rgba(44,62,107,0.40) 0%, transparent 100%),
    radial-gradient(1px   1px   at 15% 22%, rgba(74,94,143,0.30) 0%, transparent 100%),
    radial-gradient(1.4px 1.4px at 22% 35%, rgba(44,62,107,0.45) 0%, transparent 100%),
    radial-gradient(1px   1px   at 31% 18%, rgba(74,94,143,0.28) 0%, transparent 100%),
    radial-gradient(1.2px 1.2px at 42%  7%, rgba(44,62,107,0.35) 0%, transparent 100%),
    radial-gradient(1px   1px   at 53% 28%, rgba(74,94,143,0.25) 0%, transparent 100%),
    radial-gradient(1.4px 1.4px at 63% 12%, rgba(44,62,107,0.38) 0%, transparent 100%),
    radial-gradient(1px   1px   at 71% 25%, rgba(74,94,143,0.28) 0%, transparent 100%),
    radial-gradient(1.2px 1.2px at 80% 18%, rgba(44,62,107,0.32) 0%, transparent 100%),
    radial-gradient(1px   1px   at 88% 8%,  rgba(74,94,143,0.35) 0%, transparent 100%),
    radial-gradient(1px   1px   at 94% 30%, rgba(44,62,107,0.25) 0%, transparent 100%),
    radial-gradient(1px   1px   at  5% 28%, rgba(74,94,143,0.22) 0%, transparent 100%),
    radial-gradient(1.4px 1.4px at 47% 18%, rgba(44,62,107,0.32) 0%, transparent 100%),
    radial-gradient(1px   1px   at 76%  5%, rgba(74,94,143,0.35) 0%, transparent 100%),
    radial-gradient(1px   1px   at 35% 32%, rgba(44,62,107,0.20) 0%, transparent 100%);
}
.starfield::after {
  content: "";
  position: absolute; inset: 0;
  background-image:
    radial-gradient(1px 1px at 12% 8%,  rgba(44,62,107,0.20) 0%, transparent 100%),
    radial-gradient(1px 1px at 27% 18%, rgba(74,94,143,0.22) 0%, transparent 100%),
    radial-gradient(1px 1px at 48% 22%, rgba(44,62,107,0.18) 0%, transparent 100%),
    radial-gradient(1px 1px at 66% 15%, rgba(74,94,143,0.15) 0%, transparent 100%),
    radial-gradient(1px 1px at 83% 32%, rgba(44,62,107,0.20) 0%, transparent 100%),
    radial-gradient(1px 1px at 91% 18%, rgba(74,94,143,0.25) 0%, transparent 100%),
    radial-gradient(1px 1px at 38% 28%, rgba(44,62,107,0.15) 0%, transparent 100%),
    radial-gradient(1px 1px at 58% 8%,  rgba(74,94,143,0.22) 0%, transparent 100%);
}

.hero-eyebrow {
  font-family: var(--en);
  font-size: 0.82rem;
  font-style: italic;
  letter-spacing: 0.4em;
  color: var(--gold-d);
  margin-bottom: 2rem;
  opacity: 0.9;
}
.hero-title {
  font-family: "Shippori Mincho", "Noto Serif JP", serif;
  font-size: clamp(2.2rem, 5.5vw, 3.8rem);
  font-weight: 300;
  color: var(--text-d);
  line-height: 1.5;
  letter-spacing: 0.06em;
  margin-bottom: 1.4rem;
}
.hero-title em {
  font-style: normal;
  font-weight: 400;
  color: var(--lav-d);
}
.hero-rule {
  width: 80px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  margin: 0 auto 1.6rem;
}
.hero-sub {
  font-family: var(--serif);
  font-size: clamp(0.9rem, 1.8vw, 1.05rem);
  font-weight: 300;
  color: var(--text-m);
  letter-spacing: 0.12em;
  margin-bottom: 0.9rem;
  line-height: 2;
}
.hero-planets {
  font-size: 1.3rem;
  letter-spacing: 0.55em;
  color: var(--gold);
  margin-bottom: 3.5rem;
  opacity: 0.85;
}
.cta-btn {
  display: inline-block;
  padding: 1.05rem 3.2rem;
  background: rgba(255,255,255,0.5);
  border: 1px solid var(--gold);
  border-radius: 2px;
  color: var(--gold-d);
  font-family: var(--serif);
  font-size: 0.92rem;
  font-weight: 500;
  letter-spacing: 0.2em;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.35s;
  position: relative;
  overflow: hidden;
}
.cta-btn::before {
  content: "";
  position: absolute; inset: 0;
  background: var(--gold);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.35s;
  z-index: -1;
}
.cta-btn:hover::before { transform: scaleX(1); }
.cta-btn:hover { color: var(--white); border-color: var(--gold-d); }

.cta-sub {
  display: inline-block;
  margin-top: 1.4rem;
  color: var(--text-m);
  font-family: var(--serif);
  font-size: 0.82rem;
  text-decoration: none;
  letter-spacing: 0.12em;
  border-bottom: 1px solid rgba(168,156,200,0.5);
  padding-bottom: 2px;
  transition: color 0.25s, border-color 0.25s;
}
.cta-sub:hover { color: var(--lav-d); border-color: var(--lav-d); }

.scroll-cue {
  position: absolute; bottom: 2.8rem; left: 50%; transform: translateX(-50%);
  display: flex; flex-direction: column; align-items: center; gap: 0.5rem;
  color: var(--text-l);
  font-family: var(--en);
  font-size: 0.72rem;
  letter-spacing: 0.25em;
  animation: scrollBounce 2.5s ease-in-out infinite;
}
.scroll-cue svg { opacity: 0.5; }
@keyframes scrollBounce {
  0%,100% { transform: translateX(-50%) translateY(0); }
  50%      { transform: translateX(-50%) translateY(7px); }
}

/* ─── 共通セクション（明るめ3トーン） ─── */
.sec-light { background: var(--white);     color: var(--text-d); }
.sec-mid   { background: var(--base-warm); color: var(--text-d); }
.sec-dark  { background: var(--base-lav);  color: var(--text-d); }

section { padding: 7rem 2rem; }
.inner { max-width: 980px; margin: 0 auto; }
.sec-eyebrow {
  font-family: var(--en);
  font-size: 0.75rem;
  font-style: italic;
  letter-spacing: 0.35em;
  color: var(--gold);
  text-align: center;
  margin-bottom: 1rem;
}
.sec-title {
  font-family: var(--serif);
  font-size: clamp(1.5rem, 3vw, 2.1rem);
  font-weight: 400;
  text-align: center;
  letter-spacing: 0.06em;
  margin-bottom: 0.9rem;
  color: var(--text-d);
}
.sec-dark .sec-title { color: var(--text-d); }
.sec-rule {
  width: 48px; height: 1px;
  background: linear-gradient(90deg, transparent, var(--gold), transparent);
  margin: 0 auto 1.6rem;
}
.sec-lead {
  text-align: center;
  color: var(--text-m);
  font-size: 0.88rem;
  max-width: 520px;
  margin: 0 auto 4rem;
  line-height: 2.1;
}
.sec-dark .sec-lead { color: var(--text-m); }

/* ─── 惑星グリッド ─── */
.planet-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 1px;
  background: var(--cream3);
  border: 1px solid var(--cream3);
}
.planet-card {
  background: var(--cream);
  padding: 1.8rem 1.6rem;
  transition: background 0.2s;
}
.planet-card:hover { background: var(--cream2); }
.planet-sym {
  font-size: 1.5rem;
  display: block;
  margin-bottom: 0.7rem;
  line-height: 1;
}
.planet-name {
  font-family: var(--serif);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-d);
  margin-bottom: 0.5rem;
  letter-spacing: 0.05em;
}
.planet-en {
  font-family: var(--en);
  font-size: 0.8rem;
  font-style: italic;
  color: var(--gold);
  display: block;
  margin-bottom: 0.7rem;
  letter-spacing: 0.08em;
}
.planet-desc {
  font-size: 0.8rem;
  color: var(--text-m);
  line-height: 1.85;
}

/* ─── レポート内容（4商品別の詳細） ─── */
.report-detail {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 6px;
  padding: 2rem 2.2rem;
  margin-bottom: 1.4rem;
  box-shadow: 0 2px 12px rgba(58,52,80,0.04);
  transition: transform 0.25s, box-shadow 0.25s;
}
.report-detail:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(58,52,80,0.07);
}
.report-detail-free {
  background: var(--base-soft);
  border-style: dashed;
}
.report-detail-head {
  display: flex; align-items: center; gap: 1.2rem;
  padding-bottom: 1.2rem;
  margin-bottom: 1.4rem;
  border-bottom: 1px solid var(--border-l);
}
.report-detail-icon {
  font-size: 2rem; line-height: 1;
}
.report-detail-title {
  font-family: var(--serif);
  font-size: 1.15rem;
  font-weight: 500;
  color: var(--text-d);
  letter-spacing: 0.06em;
  margin-bottom: 0.3rem;
}
.report-detail-sub {
  font-size: 0.78rem;
  color: var(--gold-d);
  letter-spacing: 0.08em;
}
.report-detail-lead {
  font-size: 0.85rem;
  color: var(--text-m);
  line-height: 2;
  margin-bottom: 1.2rem;
  letter-spacing: 0.04em;
}
.report-detail-list {
  list-style: none; padding: 0; margin: 0;
}
.report-detail-list li {
  font-size: 0.82rem;
  color: var(--text-m);
  line-height: 2.1;
  padding: 0.3rem 0;
  border-bottom: 1px dashed var(--border-l);
}
.report-detail-list li:last-child { border-bottom: none; }
.report-detail-list strong {
  color: var(--text-d);
  font-weight: 500;
  margin-right: 0.4rem;
}
.report-detail-note {
  margin-top: 1.2rem;
  padding: 0.8rem 1rem;
  background: var(--base-warm);
  border-left: 2px solid var(--gold);
  font-size: 0.78rem;
  color: var(--text-m);
  line-height: 1.9;
}
/* ─── レポート内容（旧グリッド・互換用） ─── */
.what-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(270px, 1fr));
  gap: 1.6rem;
}
.what-item {
  display: flex; gap: 1.2rem; align-items: flex-start;
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 4px;
  padding: 1.6rem 1.5rem;
  box-shadow: 0 2px 12px rgba(58,52,80,0.04);
  transition: transform 0.25s, box-shadow 0.25s;
}
.what-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(58,52,80,0.08);
}
.what-num {
  font-family: var(--en);
  font-size: 2rem;
  font-style: italic;
  font-weight: 500;
  color: var(--gold);
  line-height: 1;
  flex-shrink: 0;
  width: 2.2rem;
  text-align: center;
}
.what-body strong {
  display: block;
  font-family: var(--serif);
  font-size: 0.95rem;
  font-weight: 500;
  color: var(--text-d);
  margin-bottom: 0.5rem;
  letter-spacing: 0.04em;
}
.what-body span {
  font-size: 0.82rem;
  color: var(--text-m);
  line-height: 1.95;
}

/* ─── フォームセクション ─── */
.form-outer {
  max-width: 520px;
  margin: 0 auto;
}
.form-card {
  background: var(--white);
  border: 1px solid var(--cream3);
  border-radius: 2px;
  padding: 3rem 2.8rem 2.8rem;
  box-shadow: 0 20px 60px rgba(0,0,0,0.08), 0 4px 16px rgba(0,0,0,0.05);
}
.form-hd {
  text-align: center;
  margin-bottom: 2.2rem;
}
.form-hd-title {
  font-family: var(--serif);
  font-size: 1.1rem;
  font-weight: 400;
  color: var(--text-d);
  letter-spacing: 0.1em;
  margin-bottom: 0.4rem;
}
.form-hd-sub {
  font-size: 0.78rem;
  color: var(--text-l);
  letter-spacing: 0.06em;
}
.field-label {
  display: block;
  font-size: 0.75rem;
  font-weight: 500;
  color: var(--text-m);
  letter-spacing: 0.08em;
  margin-bottom: 0.4rem;
  margin-top: 1.4rem;
}
input[type=text],
input[type=number],
select {
  width: 100%;
  padding: 0.75rem 0.9rem;
  background: var(--cream);
  border: 1px solid var(--cream3);
  border-radius: 2px;
  color: var(--text-d);
  font-family: var(--sans);
  font-size: 0.92rem;
  font-weight: 300;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
  -webkit-appearance: none;
}
input:focus, select:focus {
  border-color: var(--gold);
  background: var(--white);
  box-shadow: 0 0 0 3px rgba(184,146,58,0.08);
}
input::placeholder { color: var(--text-l); font-size: 0.82rem; }
select { cursor: pointer; }
select option { background: var(--white); color: var(--text-d); }
.row2 { display: flex; gap: 0.7rem; }
.row3 { display: flex; gap: 0.7rem; }
.row2 > div, .row3 > div { flex: 1; }
.hint {
  font-size: 0.73rem;
  color: var(--text-l);
  margin-top: 0.4rem;
  line-height: 1.65;
}
.form-rule {
  width: 100%; height: 1px;
  background: var(--cream3);
  margin: 2rem 0;
}
.btn-group { display: flex; flex-direction: column; gap: 0.7rem; }
.sr-row { display: flex; gap: 0.7rem; align-items: stretch; }
.sr-year-wrap {
  display: flex; flex-direction: column; justify-content: center;
  gap: 0.2rem; min-width: 110px;
}
.sr-year-label {
  font-size: 0.65rem; letter-spacing: 0.1em;
  color: var(--text-l); font-family: var(--serif);
}
.sr-year-select {
  padding: 0.5rem 0.4rem;
  border: 1px solid var(--cream3);
  border-radius: 2px;
  background: transparent;
  font-family: var(--serif);
  font-size: 0.85rem;
  color: var(--text-d);
  cursor: pointer;
}
.sr-row .btn-gold { flex: 1; }
.btn {
  flex: 1;
  padding: 0.95rem 0.5rem;
  border-radius: 2px;
  font-family: var(--serif);
  font-size: 0.88rem;
  font-weight: 400;
  letter-spacing: 0.1em;
  cursor: pointer;
  transition: all 0.25s;
  border: 1px solid;
}
.btn-gold {
  background: var(--gold);
  border-color: var(--gold);
  color: var(--white);
}
.btn-gold:hover { background: var(--gold-l); border-color: var(--gold-l); }
.btn-outline {
  background: transparent;
  border-color: var(--cream3);
  color: var(--text-m);
}
.btn-outline:hover { border-color: var(--gold); color: var(--gold); }
.btn-indigo {
  background: #3A3875;
  border-color: #3A3875;
  color: #fff;
  flex: 1;
}
.btn-indigo:hover { background: #4A4890; border-color: #4A4890; }
.btn:disabled { opacity: 0.45; cursor: not-allowed; }
.btn:active:not(:disabled) { transform: scale(0.99); }
/* ─── フォーム内 無料/有料ラベル区切り ─── */
.form-plan-divider {
  display: flex; align-items: center; gap: 0.9rem;
  margin: 1.6rem 0 1rem;
}
.form-plan-divider::before,
.form-plan-divider::after {
  content: ''; flex: 1; height: 1px; background: var(--border-l);
}
.form-plan-divider span {
  font-family: var(--en); font-style: italic; font-size: 0.7rem;
  letter-spacing: 0.28em; color: var(--text-l); white-space: nowrap;
}
.form-plan-divider.paid span {
  color: var(--gold-d); font-style: normal; font-size: 0.78rem;
  letter-spacing: 0.15em; font-family: var(--serif);
}
/* ─── ボタン内の価格バッジ ─── */
.btn-price {
  display: inline-block;
  padding: 2px 10px;
  margin-left: 8px;
  background: rgba(255,255,255,0.18);
  border: 1px solid rgba(255,255,255,0.35);
  border-radius: 12px;
  font-family: var(--en);
  font-size: 0.78rem;
  letter-spacing: 0.06em;
  vertical-align: middle;
}
.btn-outline .btn-price.free {
  background: rgba(123,144,196,0.15);
  border-color: var(--lav-l);
  color: var(--lav-d);
}
/* ─── ボタン下の補足テキスト ─── */
.btn-note {
  font-size: 0.7rem;
  color: var(--text-l);
  text-align: center;
  margin: -0.2rem 0 0.4rem;
  letter-spacing: 0.04em;
}
.btn-note a {
  color: var(--gold-d);
  text-decoration: underline;
  text-decoration-color: rgba(184,152,90,0.4);
}
.btn-note a:hover { text-decoration-color: var(--gold-d); }
/* ─── 出生チャート（有料）ボタン ─── */
.btn-natal {
  background: var(--gold-d);
  border-color: var(--gold-d);
  color: #fff;
}
.btn-natal:hover:not(:disabled) {
  background: var(--gold);
  border-color: var(--gold);
}
#status {
  text-align: center;
  margin-top: 1.2rem;
  min-height: 1.8rem;
  font-size: 0.82rem;
  line-height: 1.7;
  color: var(--text-m);
}
.status-ok  { color: #4A8A5A; }
.status-err { color: #A04848; }
.status-wait { color: var(--gold); }
.loading-dots::after {
  content: '';
  animation: dots 1.5s steps(4, end) infinite;
}
@keyframes dots {
  0%   { content: ''; }
  25%  { content: '.'; }
  50%  { content: '..'; }
  75%  { content: '...'; }
}

/* ─── フッター ─── */
footer {
  background: var(--base-warm);
  border-top: 1px solid var(--border);
  padding: 4rem 2rem;
  text-align: center;
}
.footer-rule {
  width: 40px; height: 1px;
  background: var(--gold);
  margin: 0 auto 1.4rem;
}
.footer-logo {
  font-family: var(--serif);
  font-size: 0.95rem;
  color: var(--gold-d);
  letter-spacing: 0.2em;
  margin-bottom: 0.6rem;
}
.footer-planets {
  font-size: 0.95rem;
  color: var(--gold);
  letter-spacing: 0.5em;
  margin-bottom: 1.2rem;
  opacity: 0.7;
}
.footer-copy {
  font-size: 0.72rem;
  color: var(--text-l);
  letter-spacing: 0.08em;
}
.footer-links {
  display: flex;
  justify-content: center;
  gap: 1.6rem;
  flex-wrap: wrap;
  margin-bottom: 1.2rem;
}
.footer-links a {
  font-size: 0.72rem;
  color: var(--text-l);
  text-decoration: none;
  letter-spacing: 0.06em;
  border-bottom: 1px solid transparent;
  transition: color 0.2s, border-color 0.2s;
}
.footer-links a:hover {
  color: var(--gold-d);
  border-bottom-color: var(--gold);
}

/* ─── レポートカード ─── */
.report-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
  gap: 2rem;
}
.report-card {
  background: var(--white);
  border: 1px solid var(--border);
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: transform 0.3s, border-color 0.3s, box-shadow 0.3s;
  display: flex;
  flex-direction: column;
  position: relative;
  box-shadow: 0 2px 12px rgba(58,52,80,0.04);
}
.report-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 14px 36px rgba(58,52,80,0.10);
}
.report-card.free:hover      { border-color: var(--lav); }
.report-card.natal:hover     { border-color: var(--rose); }
.report-card.sr:hover        { border-color: var(--gold); }
.report-card.lifecycle:hover { border-color: var(--lav); }

.promo-ribbon {
  position:absolute; top:14px; right:-30px;
  background: linear-gradient(135deg, #D4B987, #B8985A);
  color:#FFFFFF; font-size:0.62rem; font-weight:700;
  letter-spacing:0.2em; padding:3px 36px; transform: rotate(35deg);
  font-family: var(--sans); z-index:5;
  box-shadow: 0 2px 6px rgba(58,52,80,0.18);
}
.price-box {
  margin: 0 0 1.2rem; padding: 0.9rem 0;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  text-align: center;
}
.price-box.price-free { border-top-color: rgba(168,156,200,0.35); border-bottom-color: rgba(168,156,200,0.35); }
.price-main {
  font-family: var(--en); font-size: 2rem; font-weight: 500;
  color: var(--gold-d); letter-spacing: 0.04em; line-height: 1;
}
.price-free .price-main { color: var(--lav-d); font-family: var(--serif); font-size: 1.6rem; }
.price-sub {
  font-size: 0.7rem; color: var(--text-l);
  letter-spacing: 0.08em; margin-top: 0.4rem;
}
.report-card.free .report-accent { background: linear-gradient(90deg, var(--lav), var(--lav-l)); }
.free-badge { background:rgba(168,156,200,0.12); color:var(--lav-d); border:1px solid rgba(168,156,200,0.3); }
.free  .report-cta { color: var(--lav-d); }

.sample-link {
  display: block; text-align: center;
  margin-top: 0.6rem; padding: 0.5rem 0;
  font-size: 0.74rem; letter-spacing: 0.1em;
  color: var(--text-m);
  text-decoration: none;
  border-bottom: 1px solid var(--border);
  transition: color 0.2s, border-color 0.2s;
}
.sample-link:hover {
  color: var(--gold-d);
  border-bottom-color: var(--gold);
}
.sample-link::after { content: " ▸"; opacity: 0.7; }
.report-accent {
  height: 3px;
  width: 100%;
}
.natal     .report-accent { background: linear-gradient(90deg, var(--rose), var(--rose-l)); }
.sr        .report-accent { background: linear-gradient(90deg, var(--gold-d), var(--gold-l)); }
.lifecycle .report-accent { background: linear-gradient(90deg, var(--lav-d), var(--lav-l)); }
.report-info { padding: 1.8rem 1.6rem 1.4rem; flex:1; display:flex; flex-direction:column; }
.report-info h3 {
  font-family:var(--serif); font-size:1.15rem; font-weight:500;
  color:var(--text-d); letter-spacing:0.06em; margin-bottom:0.3rem;
}
.report-sub {
  font-family:var(--en); font-style:italic; font-size:0.74rem;
  color:var(--gold-d); letter-spacing:0.14em; margin-bottom:1rem;
}
.report-meta {
  display: flex; gap:0.8rem; align-items:center; margin-bottom:1.1rem; flex-wrap:wrap;
}
.report-badge {
  display:inline-block; font-size:0.68rem; padding:0.2rem 0.6rem;
  border-radius:2px; letter-spacing:0.06em;
}
.natal-badge     { background:rgba(196,154,160,0.15); color:#9A6B72; border:1px solid rgba(196,154,160,0.35); }
.sr-badge        { background:rgba(184,152,90,0.12);  color:var(--gold-d); border:1px solid rgba(184,152,90,0.35); }
.lifecycle-badge { background:rgba(168,156,200,0.12); color:var(--lav-d); border:1px solid rgba(168,156,200,0.35); }
.report-pages {
  font-size:0.72rem; color:var(--text-l); letter-spacing:0.06em;
}
.report-desc {
  font-size:0.82rem; color:var(--text-m); line-height:2; margin-bottom:1.1rem;
}
.report-includes { list-style:none; padding:0; display:flex; flex-direction:column; gap:0.4rem; flex:1; }
.report-includes li { font-size:0.78rem; color:var(--text-m); letter-spacing:0.03em; }
.report-cta {
  margin-top:1.4rem; padding-top:1.1rem;
  border-top:1px solid var(--border);
  font-size:0.78rem; letter-spacing:0.12em;
  text-align:center;
  font-weight: 500;
  transition: color 0.2s;
}
.natal     .report-cta { color:#9A6B72; }
.sr        .report-cta { color:var(--gold-d); }
.lifecycle .report-cta { color:var(--lav-d); }
.report-card:hover .report-cta { opacity:1; }
.report-cta::after { content:" →"; }

/* ─── レスポンシブ ─── */
@media (max-width: 660px) {
  nav { padding: 0 1.4rem; }
  .nav-links { display: none; }
  .form-card { padding: 2rem 1.4rem; }
  .btn-group { flex-direction: column; }
  .row3 { flex-wrap: wrap; }
}
  </style>
</head>
<body>

<!-- ナビゲーション -->
<nav>
  <a class="nav-logo" href="#hero">MOONLOG</a>
  <ul class="nav-links">
    <li><a href="#about">このサービスについて</a></li>
    <li><a href="#profile">運営者について</a></li>
    <li><a href="/blog">ブログ</a></li>
    <li><a href="/glossary">用語解説</a></li>
    <li><a href="/faq">よくある質問</a></li>
    <li><a href="#form-section">星読みをはじめる</a></li>
  </ul>
</nav>

<!-- ヒーロー -->
<section id="hero">
  <div class="starfield"></div>

  <p class="hero-eyebrow">Moon × Log — Birth Chart Reading</p>
  <h1 class="hero-title">
    自分を知るための<br>
    <em>静かな航海日誌</em>
  </h1>
  <div class="hero-rule"></div>
  <p class="hero-sub">
    迷ってもいいし、見失ってもいい。<br>
    そんなときに、自分という地図を確かめるためのツールです。
  </p>
  <p class="hero-planets">☉ &nbsp; ☽ &nbsp; ☿ &nbsp; ♀ &nbsp; ♂ &nbsp; ♃ &nbsp; ♄</p>
  <a href="#form-section" class="cta-btn">無料で星読みをはじめる</a>
  <a href="#reports" class="cta-sub">▸ レポートについて詳しく</a>

  <div class="scroll-cue">
    <span>scroll</span>
    <svg width="14" height="14" viewBox="0 0 14 14" fill="none">
      <path d="M2 5l5 5 5-5" stroke="currentColor" stroke-width="1.2" stroke-linecap="round"/>
    </svg>
  </div>
</section>

<!-- MOONLOGとは -->
<section id="moonlog-def" class="sec-light">
  <div class="inner" style="max-width:720px;">
    <p class="sec-eyebrow">What is MOONLOG</p>
    <h2 class="sec-title">MOONLOGとは</h2>
    <div class="sec-rule"></div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:3rem;margin-bottom:3rem;">
      <div style="text-align:center;padding:2rem 1.5rem;background:var(--white);border:1px solid var(--border);border-radius:2px;box-shadow:0 2px 12px rgba(58,52,80,0.04);">
        <div style="font-family:var(--en);font-size:2.2rem;font-style:italic;color:var(--gold-d);margin-bottom:1rem;letter-spacing:0.1em;">MOON</div>
        <p style="font-size:0.84rem;color:var(--text-m);line-height:2;letter-spacing:0.04em;">
          昼間の空にひっそりと存在する、<br>はかなげで静かな月。<br>
          見えなくても、引力で海の潮を動かす。<br>
          目に見えない力で、確かに何かを動かすもの。
        </p>
      </div>
      <div style="text-align:center;padding:2rem 1.5rem;background:var(--white);border:1px solid var(--border);border-radius:2px;box-shadow:0 2px 12px rgba(58,52,80,0.04);">
        <div style="font-family:var(--en);font-size:2.2rem;font-style:italic;color:var(--gold-d);margin-bottom:1rem;letter-spacing:0.1em;">LOG</div>
        <p style="font-size:0.84rem;color:var(--text-m);line-height:2;letter-spacing:0.04em;">
          かつて船乗りは、月と星だけを頼りに<br>大海原の航路を定めた。<br>
          その記録が「航海日誌（ship's log）」。<br>
          感情ではなく、客観的なデータで自分を記録すること。
        </p>
      </div>
    </div>
    <div style="text-align:center;border-top:1px solid var(--border);padding-top:2.5rem;">
      <p style="font-family:var(--serif);font-size:1.05rem;color:var(--gold-d);letter-spacing:0.1em;line-height:2.2;">
        生まれた瞬間の天体データを読み解き、<br>
        自分でも気づいていなかった傾向に光を当てる。<br>
        月が海を動かすように、言葉が自分の内側を静かに動かす。<br>
        それが、MOONLOGです。
      </p>
    </div>
  </div>
</section>

<!-- レポート一覧と料金 -->
<section id="reports" class="sec-dark" style="padding-bottom:8rem;">
  <div class="inner">
    <p class="sec-eyebrow">Reports & Pricing</p>
    <h2 class="sec-title">レポートの種類と料金</h2>
    <div class="sec-rule"></div>
    <p class="sec-lead">何者か、どう生きるか、今年は何が来るか。<br>3つの視点から、自分という地図を読む。</p>

    <div class="report-grid">

      <!-- タイプ診断（無料・入口） -->
      <div class="report-card free" onclick="document.getElementById('form-section').scrollIntoView({behavior:'smooth'})">
        <div class="report-accent" style="background: linear-gradient(90deg, #E89C5A, #F4C28B);"></div>
        <div class="report-info">
          <h3>月タイプ診断</h3>
          <p class="report-sub">Your Moon Type — 月星座でわかる12タイプ</p>
          <div class="report-meta">
            <span class="report-badge free-badge">月・動物タイプ</span>
            <span class="report-pages">すぐにわかる</span>
          </div>
          <div class="price-box price-free">
            <div class="price-main">無料</div>
            <div class="price-sub">登録不要・ぱっとわかる</div>
          </div>
          <p class="report-desc">
            「あなたは◯◯」。生まれた瞬間の月から、素のあなたを動物のタイプでひと目で。いちばん身軽な、自分を知る入口です。
          </p>
          <ul class="report-includes">
            <li>✦ あなたのタイプ（動物＋ひとこと）</li>
            <li>✦ 月星座からの性格の読み解き</li>
            <li>✦ 今のあなたへの一言</li>
          </ul>
          <div class="report-cta">タイプを調べる</div>
        </div>
      </div>

      <!-- 出生チャート 無料体験版 -->
      <div class="report-card free" onclick="document.getElementById('form-section').scrollIntoView({behavior:'smooth'})">
        <div class="report-accent"></div>
        <div class="report-info">
          <h3>出生チャート 無料体験版</h3>
          <p class="report-sub">Free Light Reading</p>
          <div class="report-meta">
            <span class="report-badge free-badge">☉ ☽ の2天体</span>
            <span class="report-pages">A4換算 約8ページ</span>
          </div>
          <div class="price-box price-free">
            <div class="price-main">無料</div>
            <div class="price-sub">登録不要・すぐに読めます</div>
          </div>
          <p class="report-desc">
            まず、あなたの太陽星座から。生まれ持った気質のさわりを読んで、星読みの世界をのぞいてみてください。
          </p>
          <ul class="report-includes">
            <li>✦ 太陽：人生のテーマ</li>
            <li>✦ 月：感情と内面</li>
            <li>✦ 水星：思考とコミュニケーション</li>
          </ul>
          <div class="report-cta">無料ではじめる</div>
        </div>
      </div>

      {% if show_paid %}
      <!-- 出生チャート（有料）-->
      <div class="report-card natal" onclick="document.getElementById('form-section').scrollIntoView({behavior:'smooth'})">
        <div class="report-accent"></div>
        <div class="promo-ribbon">オープン記念</div>
        <div class="report-info">
          <h3>出生チャート</h3>
          <p class="report-sub">あなたが何者かを知る</p>
          <div class="report-meta">
            <span class="report-badge natal-badge">基本 / いつでも</span>
            <span class="report-pages">A4換算 約20ページ</span>
          </div>
          <div class="price-box">
            <div class="price-main">¥980</div>
            <div class="price-sub">通常価格 ¥3,980 を予定</div>
          </div>
          <p class="report-desc">
            自分が何者なのか——普段当たり前にやっていること、繰り返し起こるパターン。その「なぜ」が、生まれた瞬間の星の配置から見えてきます。欠点ではなく、生まれ持ったあなたの形を知る。
          </p>
          <ul class="report-includes">
            <li>✦ 各惑星の詳細プロフィール</li>
            <li>✦ 強みと成長のヒント</li>
            <li>✦ 天体間のアスペクト</li>
            <li>✦ 総合プロフィール</li>
          </ul>
          <div class="report-cta">レポートを購入する</div>
          <a href="/sample/natal" target="_blank" class="sample-link" onclick="event.stopPropagation()">サンプルを見る</a>
        </div>
      </div>

      <!-- ソーラーリターン（有料）-->
      <div class="report-card sr" onclick="document.getElementById('form-section').scrollIntoView({behavior:'smooth'})">
        <div class="report-accent"></div>
        <div class="promo-ribbon">オープン記念</div>
        <div class="report-info">
          <h3>2026年 星読み</h3>
          <p class="report-sub">今年のあなたを知る</p>
          <div class="report-meta">
            <span class="report-badge sr-badge">年間 / 誕生日ごとに</span>
            <span class="report-pages">A4換算 約18ページ</span>
          </div>
          <div class="price-box">
            <div class="price-main">¥980</div>
            <div class="price-sub">通常価格 ¥3,980 を予定</div>
          </div>
          <p class="report-desc">
            毎年変わる星の配置。2026年のあなたのテーマ、チャレンジに向く時期、休むべき時期——1年の流れを知れば、毎日の選択がぐっと楽になります。
          </p>
          <ul class="report-includes">
            <li>✦ 今年のメインテーマ</li>
            <li>✦ 力が発揮される分野</li>
            <li>✦ 注意すべきパターン</li>
            <li>✦ 星からのメッセージ</li>
          </ul>
          <div class="report-cta">レポートを購入する</div>
          <a href="/sample/sr" target="_blank" class="sample-link" onclick="event.stopPropagation()">サンプルを見る</a>
        </div>
      </div>

      <!-- ライフサイクル（一時非表示・2026-05-11） 7月以降に大改修して復活予定
      <div class="report-card lifecycle" onclick="document.getElementById('form-section').scrollIntoView({behavior:'smooth'})">
        ... 元のライフサイクルカードのHTMLはこのコメント内に保管 ...
      </div>
      -->

      <!-- 3分野レポート（仕事・お金・恋愛） -->
      <div class="report-card lifecycle" onclick="document.getElementById('form-section').scrollIntoView({behavior:'smooth'})">
        <div class="report-accent"></div>
        <div class="promo-ribbon">オープン記念</div>
        <div class="report-info">
          <h3>仕事・お金・恋愛</h3>
          <p class="report-sub">あなたの3つの分野レポート</p>
          <div class="report-meta">
            <span class="report-badge lifecycle-badge">分野別 / 関心ごとに</span>
            <span class="report-pages">A4換算 約15ページ</span>
          </div>
          <div class="price-box">
            <div class="price-main">¥980</div>
            <div class="price-sub">通常価格 ¥3,980 を予定</div>
          </div>
          <p class="report-desc">
            仕事には仕事を司る星、お金にはお金を司る星、愛には愛を司る星があります。同じ「あなた」の中でも、分野ごとに使われている星が違う——その3つを一冊にまとめた読みもの。
          </p>
          <ul class="report-includes">
            <li>✦ 仕事観の核と、輝く場面・天職の方向</li>
            <li>✦ お金の感覚と、豊かさが育つ場所</li>
            <li>✦ 愛し方の核と、求める関係性</li>
            <li>✦ 3章を統合した「あなた」の全体像</li>
          </ul>
          <div class="report-cta">レポートを購入する</div>
          <a href="/sample/field_report" target="_blank" class="sample-link" onclick="event.stopPropagation()">サンプルを見る</a>
        </div>
      </div>
      {% endif %}

      {% if not show_paid %}
      <!-- Coming Soon カード（ソフトローンチ期間） -->
      <div class="report-card" style="grid-column: span 2; background:rgba(184,152,88,.06); border:2px dashed var(--gold); padding:2.5rem 2rem; text-align:center;">
        <div class="report-info">
          <h3 style="color:var(--gold-d);">✨ 有料レポートは {{ release_date_dot }} リリース</h3>
          <p style="margin-top:1rem;font-size:0.95rem;color:var(--text-m);line-height:1.9;">
            出生チャート・年間星読み・仕事/お金/恋愛 3分野レポート——<br>
            ただいま最終仕上げ中です。リリース日まで、出生チャート 無料体験版でお楽しみください。
          </p>
          <p style="margin-top:1rem;font-size:0.85rem;color:var(--text-l);">
            <a href="/sample/natal" target="_blank" style="color:var(--gold-d);text-decoration:underline;margin:0 0.5rem;">出生チャート サンプル</a>
            <a href="/sample/sr" target="_blank" style="color:var(--gold-d);text-decoration:underline;margin:0 0.5rem;">年間星読み サンプル</a>
            <a href="/sample/field_report" target="_blank" style="color:var(--gold-d);text-decoration:underline;margin:0 0.5rem;">3分野レポート サンプル</a>
          </p>
        </div>
      </div>
      {% endif %}

    </div>

    <p style="text-align:center;margin-top:3rem;font-size:0.78rem;color:var(--text-l);letter-spacing:0.08em;">
      ※ オープン記念価格は予告なく変更となる場合があります。価格は順次改定予定です。
    </p>
  </div>
</section>

<!-- 入力フォーム -->
<section id="form-section" class="sec-mid">
  <div class="inner">
    <p class="sec-eyebrow">Free Reading</p>
    <h2 class="sec-title">星読みをはじめる</h2>
    <div class="sec-rule"></div>
    <p class="sec-lead" style="color:var(--text-m);">
      生年月日・出生時刻・出生地を入力してください。<br>
      あなただけのレポートを無料で生成します。
    </p>

    <div class="form-outer">
      <div class="form-card">
        <div class="form-hd">
          <div class="form-hd-title">出生データを入力する</div>
          <div class="form-hd-sub">すべての項目をご入力ください</div>
        </div>

        <form id="form" method="post" action="/preview">
          <label class="field-label">お名前</label>
          <input type="text" name="name" placeholder="例：はなこ / Hana" required>
          <p class="hint" style="margin:4px 0 12px;font-size:0.78rem;color:#8c7858;">※ ニックネームでも構いません。レポートの冒頭に表示される呼び方です。本名でなくても大丈夫です。</p>

          <label class="field-label">生年月日</label>
          <div class="row3">
            <div><input type="number" name="year"  placeholder="年（1900〜2025）" min="1900" max="2025" required></div>
            <div><input type="number" name="month" placeholder="月（1〜12）"      min="1" max="12" required></div>
            <div><input type="number" name="day"   placeholder="日（1〜31）"      min="1" max="31" required></div>
          </div>

          <label class="field-label">出生時刻</label>
          <div class="row2">
            <div><input type="number" name="hour"   placeholder="時（0〜23・不明なら12）" min="0" max="23" value="12" required></div>
            <div><input type="number" name="minute" placeholder="分（0〜59）" min="0" max="59" value="0"  required></div>
          </div>
          <p class="hint">※ 出生時刻が不明な場合は 12:00 のままでお進みください</p>

          <label class="field-label">出生地 <span style="font-weight:400;font-size:0.78rem;color:#8c7858;">（※日本国内のみ対応）</span></label>
          <div class="row2" style="margin-bottom:0;">
            <div>
              <select id="pref_select" onchange="updateCities(this.value)">
                <option value="">都道府県</option>
                <option value="北海道">北海道</option>
                <option value="青森県">青森県</option><option value="岩手県">岩手県</option>
                <option value="宮城県">宮城県</option><option value="秋田県">秋田県</option>
                <option value="山形県">山形県</option><option value="福島県">福島県</option>
                <option value="茨城県">茨城県</option><option value="栃木県">栃木県</option>
                <option value="群馬県">群馬県</option><option value="埼玉県">埼玉県</option>
                <option value="千葉県">千葉県</option><option value="東京都">東京都</option>
                <option value="神奈川県">神奈川県</option><option value="新潟県">新潟県</option>
                <option value="富山県">富山県</option><option value="石川県">石川県</option>
                <option value="福井県">福井県</option><option value="山梨県">山梨県</option>
                <option value="長野県">長野県</option><option value="岐阜県">岐阜県</option>
                <option value="静岡県">静岡県</option><option value="愛知県">愛知県</option>
                <option value="三重県">三重県</option><option value="滋賀県">滋賀県</option>
                <option value="京都府">京都府</option><option value="大阪府">大阪府</option>
                <option value="兵庫県">兵庫県</option><option value="奈良県">奈良県</option>
                <option value="和歌山県">和歌山県</option><option value="鳥取県">鳥取県</option>
                <option value="島根県">島根県</option><option value="岡山県">岡山県</option>
                <option value="広島県">広島県</option><option value="山口県">山口県</option>
                <option value="徳島県">徳島県</option><option value="香川県">香川県</option>
                <option value="愛媛県">愛媛県</option><option value="高知県">高知県</option>
                <option value="福岡県">福岡県</option><option value="佐賀県">佐賀県</option>
                <option value="長崎県">長崎県</option><option value="熊本県">熊本県</option>
                <option value="大分県">大分県</option><option value="宮崎県">宮崎県</option>
                <option value="鹿児島県">鹿児島県</option><option value="沖縄県">沖縄県</option>
              </select>
            </div>
            <div>
              <select name="city" id="city_select" onchange="updateLatLng(this)">
                <option value="">市区町村</option>
              </select>
            </div>
          </div>
          <input type="hidden" name="lat" id="lat_field" value="35.6762">
          <input type="hidden" name="lng" id="lng_field" value="139.6503">
          <p class="hint">※ 一覧にない場合は最寄りの市区町村を選択してください</p>

          <div class="form-rule"></div>

          <div class="btn-group">

            <!-- 無料 -->
            <div class="form-plan-divider">
              <span>まず無料でためす</span>
            </div>
            <button class="btn" type="submit"
                    formaction="/type/result" formtarget="_blank" id="btn-type"
                    style="background:#1a2740 !important;color:#ffffff !important;border:1px solid #1a2740;font-weight:700;font-size:0.95rem;">
              🌙&nbsp;<span style="background:#bd9a48;color:#1a2740;padding:3px 10px;border-radius:10px;font-size:0.72rem;margin-right:8px;font-weight:700;letter-spacing:0.05em;display:inline-block;">おすすめ</span><span style="color:#ffffff;font-weight:700;">月タイプ診断（動物でわかる）</span>&nbsp;<span style="background:#bd9a48;color:#1a2740;font-weight:700;padding:3px 10px;border-radius:10px;font-size:0.78rem;display:inline-block;">無料</span>
            </button>
            <p class="btn-note">月星座から、あなたのタイプをひと目で／登録不要</p>
            <button class="btn" type="submit"
                    formaction="/preview" formtarget="_blank" id="btn-html"
                    style="background:#fff8e7;color:#1a2740;border:1.5px solid #bd9a48;font-weight:600;font-size:0.95rem;">
              ✦&nbsp;<span style="color:#1a2740;font-weight:600;">出生チャート 無料体験版を見る</span>&nbsp;<span style="background:#bd9a48;color:#1a2740;font-weight:700;padding:3px 10px;border-radius:10px;font-size:0.78rem;display:inline-block;">無料</span>
            </button>
            <p class="btn-note">太陽・月の2天体のみ／登録不要</p>

            {% if show_paid %}
            <!-- 有料 -->
            <div class="form-plan-divider paid">
              <span>有料レポート（各¥980）</span>
            </div>

            <div class="email-field" style="margin:14px 0 18px;padding:14px 16px;background:#fffbf3;border:1px solid #e7d4a5;border-radius:8px;">
              <label for="paid_email" style="display:block;font-size:0.85rem;color:#5A3818;font-weight:600;margin-bottom:6px;">
                📧 PDF送付先メールアドレス <span style="color:#bd9a48;font-size:0.78rem;font-weight:500;">（有料レポート購入時のみ必須）</span>
              </label>
              <input type="email" name="email" id="paid_email" inputmode="email" autocomplete="email"
                     placeholder="your-name@example.com"
                     style="width:100%;padding:10px 12px;font-size:1rem;border:1px solid #d5c5a3;border-radius:6px;background:#fff;color:#3a2818;">
              <p style="margin:6px 0 0;font-size:0.75rem;color:#8c7858;">購入後、このアドレスにPDFをお届けします。</p>
              <div id="paid_email_error" style="display:none;margin-top:8px;padding:8px 12px;background:#fdecea;border-left:3px solid #c0392b;border-radius:4px;color:#a02818;font-size:0.85rem;font-weight:600;"></div>
            </div>

            <button class="btn btn-natal" type="submit"
                    formaction="/checkout/natal" id="btn-natal"
                    title="Stripeで決済 → ご購入後にレポート表示">
              🌟 &nbsp;出生チャート（フル版）　<span class="btn-price">¥980</span>
            </button>
            <p class="btn-note">7惑星すべて＋総合まとめ／<a href="/sample/natal" target="_blank">サンプルを見る</a></p>

            <div class="sr-row">
              <div class="sr-year-wrap">
                <label class="sr-year-label">何年の星読み？</label>
                <select name="sr_year" id="sr_year" class="sr-year-select"></select>
              </div>
              <button class="btn btn-gold" type="submit"
                      formaction="/solar_return" formtarget="_blank" id="btn-sr">
                ☀ &nbsp;2026年 星読み　<span class="btn-price">¥980</span>
              </button>
            </div>
            <p class="btn-note">1年間のテーマと流れ／<a href="/sample/sr" target="_blank">サンプルを見る</a></p>

            <button class="btn btn-indigo" type="submit"
                    formaction="/field_report" formtarget="_blank" id="btn-fr">
              💼 &nbsp;仕事・お金・恋愛　<span class="btn-price">¥980</span>
            </button>
            <p class="btn-note">3つの分野を一冊で／<a href="/sample/field_report" target="_blank">サンプルを見る</a></p>
            {% else %}
            <!-- ソフトローンチ期間：有料導線なし -->
            <div class="form-plan-divider paid">
              <span>有料レポート（{{ release_date_dot }} リリース予定）</span>
            </div>
            <p style="text-align:center;color:var(--text-l);font-size:0.88rem;padding:1.5rem 1rem;background:rgba(184,152,88,.05);border:1px dashed var(--gold);border-radius:4px;line-height:1.85;">
              出生チャート・年間星読み・3分野レポートは<br>
              <strong style="color:var(--gold-d);">{{ release_date_jp }}</strong> よりご購入いただけます。<br>
              <small>※ サンプルレポートは上のリンクからご覧いただけます。</small>
            </p>
            {% endif %}

          </div>
        </form>
        <div id="status"></div>
      </div>
    </div>
  </div>
</section>

<!-- レポート内容 -->
<section id="what" class="sec-dark">
  <div class="inner">
    <p class="sec-eyebrow">About the Reports</p>
    <h2 class="sec-title">PDFレポートでわかること</h2>
    <div class="sec-rule"></div>
    <p class="sec-lead">
      それぞれのレポートで、読み取れる内容が異なります。<br>
      生成されたレポートはPDFでお手元にお届けします。
    </p>

    <!-- 出生チャート -->
    <div class="report-detail">
      <div class="report-detail-head">
        <div class="report-detail-icon">🌟</div>
        <div>
          <h3 class="report-detail-title">出生チャート</h3>
          <p class="report-detail-sub">あなたが何者かを知る　／　¥980</p>
        </div>
      </div>
      <div class="report-detail-body">
        <p class="report-detail-lead">
          7つの惑星すべて＋総合まとめを統合した、あなたの「核」を読み解く基本レポート。
        </p>
        <ul class="report-detail-list">
          <li>☉ <strong>太陽</strong>：人生のテーマと自己表現のスタイル</li>
          <li>☽ <strong>月</strong>：感情のクセと心の安らぎどころ</li>
          <li>☿ <strong>水星</strong>：思考の特徴とコミュニケーションの傾向</li>
          <li>♀ <strong>金星</strong>：愛と喜びのかたち、美意識</li>
          <li>♂ <strong>火星</strong>：行動力と情熱の向け方</li>
          <li>♃ <strong>木星</strong>：成長の方向と幸運の領域</li>
          <li>♄ <strong>土星</strong>：人生の課題と魂の成熟テーマ</li>
          <li>🌟 <strong>総合プロフィール</strong>：7惑星を統合した「あなたという人」</li>
          <li>🔮 <strong>ホロスコープチャート</strong>：生まれた瞬間の天体配置図</li>
        </ul>
      </div>
    </div>

    <!-- ライフサイクル（一時非表示・2026-05-11 大改修中） -->
    <!--
    <div class="report-detail">
      ... 元のライフサイクル詳細セクションはここに保管 ...
    </div>
    -->

    <!-- 2026年星読み -->
    <div class="report-detail">
      <div class="report-detail-head">
        <div class="report-detail-icon">🌅</div>
        <div>
          <h3 class="report-detail-title">2026年 星読み</h3>
          <p class="report-detail-sub">今年のあなたを知る　／　¥980</p>
        </div>
      </div>
      <div class="report-detail-body">
        <p class="report-detail-lead">
          誕生日を起点にした1年間のテーマと流れを、8つの惑星から読み解く年間レポート。
        </p>
        <ul class="report-detail-list">
          <li>☀️ <strong>今年のあなた</strong>：太陽が照らす今年のメインテーマ</li>
          <li>💼 <strong>今年の仕事運</strong>：土星・火星・水星・木星から読み解く職場のテーマ</li>
          <li>🌙 <strong>感情・プライベート・家族</strong>：月が示す心の重心</li>
          <li>✦ <strong>仕事・学び・コミュニケーション</strong>：水星のスタイル</li>
          <li>🌹 <strong>愛・パートナーシップ・喜び</strong>：金星のかたち</li>
          <li>🔥 <strong>行動・情熱・エネルギー</strong>：火星が向かう分野</li>
          <li>⭐ <strong>成長・チャンス・広がり</strong>：木星のラッキーゾーン</li>
          <li>🌿 <strong>課題・成熟・乗り越え方</strong>：土星の魂の成長テーマ</li>
        </ul>
      </div>
    </div>

  </div>
</section>

<!-- 7惑星 -->
<section id="planets" class="sec-light">
  <div class="inner">
    <p class="sec-eyebrow">The Seven Planets</p>
    <h2 class="sec-title">7つの星が照らす、あなたの世界</h2>
    <div class="sec-rule"></div>
    <p class="sec-lead">
      西洋占星術では、7つの惑星がそれぞれ人生の異なる側面を象徴します。<br>
      生まれた瞬間の天体配置から、すべての星のメッセージを読み解きます。
    </p>
    <div class="planet-grid">
      <div class="planet-card">
        <span class="planet-sym" style="color:#B8923A;">☉</span>
        <div class="planet-name">太陽</div>
        <span class="planet-en">Sun</span>
        <div class="planet-desc">社会的な顔・人生の目的。あなたが輝くとき、どのような存在として世界に現れるかを示します。</div>
      </div>
      <div class="planet-card">
        <span class="planet-sym" style="color:#7878A8;">☽</span>
        <div class="planet-name">月</div>
        <span class="planet-en">Moon</span>
        <div class="planet-desc">感情・内面の反応パターン。安心を感じるとき、あなたの心がどのように動くかを映します。</div>
      </div>
      <div class="planet-card">
        <span class="planet-sym" style="color:#6888B0;">☿</span>
        <div class="planet-name">水星</div>
        <span class="planet-en">Mercury</span>
        <div class="planet-desc">思考・言葉・コミュニケーション。知性がどのように働き、どのように表現するかを示します。</div>
      </div>
      <div class="planet-card">
        <span class="planet-sym" style="color:#B07888;">♀</span>
        <div class="planet-name">金星</div>
        <span class="planet-en">Venus</span>
        <div class="planet-desc">愛情・美意識・喜び。何を美しいと感じ、どのように愛し愛されるかを照らします。</div>
      </div>
      <div class="planet-card">
        <span class="planet-sym" style="color:#B06848;">♂</span>
        <div class="planet-name">火星</div>
        <span class="planet-en">Mars</span>
        <div class="planet-desc">情熱・行動力・欲求エネルギー。何のために動き、どのように挑戦するかを示します。</div>
      </div>
      <div class="planet-card">
        <span class="planet-sym" style="color:#A89050;">♃</span>
        <div class="planet-name">木星</div>
        <span class="planet-en">Jupiter</span>
        <div class="planet-desc">発展・幸運・拡大の方向。人生が自然と豊かになっていく領域とその方法を示します。</div>
      </div>
      <div class="planet-card">
        <span class="planet-sym" style="color:#7870A0;">♄</span>
        <div class="planet-name">土星</div>
        <span class="planet-en">Saturn</span>
        <div class="planet-desc">課題・成長・魂のテーマ。時間をかけて向き合うことで本物の強さが生まれる場所を示します。</div>
      </div>
    </div>
  </div>
</section>

<!-- このサービスについて -->
<section id="about" class="sec-light">
  <div class="inner" style="max-width:720px;">
    <p class="sec-eyebrow">About</p>
    <h2 class="sec-title">このサービスについて</h2>
    <div class="sec-rule"></div>

    <div style="margin-bottom:3rem;">
      <h3 style="font-family:var(--serif);font-size:1.15rem;font-weight:400;color:var(--text-d);letter-spacing:0.06em;margin-bottom:1.2rem;">自分の得意が、わからない。</h3>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;margin-bottom:1rem;">
        「何が向いているのかわからない」「好きなことはあるけど、それが仕事になるとは思えない」
      </p>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;">
        真面目に生きてきたのに、なぜかずっとどこかが噛み合わない気がする。<br>
        努力してきたのに、自分が何者かわからないまま年齢だけが重なっていく。
      </p>
    </div>

    <div style="margin-bottom:3rem;">
      <h3 style="font-family:var(--serif);font-size:1.15rem;font-weight:400;color:var(--text-d);letter-spacing:0.06em;margin-bottom:1.2rem;">星読みは、占いではなくフレームワークです。</h3>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;margin-bottom:1rem;">
        生まれた瞬間の天体配置は、その人の「傾向」を読むためのデータです。<br>
        「当たる・当たらない」ではなく、「こういう資質を持って生まれた人は、こういう環境で力を発揮しやすい」という読み方をします。
      </p>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;">
        社会に出てから身につけてきた「こうあるべき自分」ではなく、<br>
        <strong>生まれながらに持っている自分の設計図</strong>を、もう一度確認する作業です。
      </p>
    </div>

    <div style="background:var(--cream2);padding:2rem;border-left:3px solid var(--gold);margin-bottom:3rem;">
      <h3 style="font-family:var(--serif);font-size:1rem;font-weight:500;color:var(--text-d);letter-spacing:0.06em;margin-bottom:1rem;">こんな壁を感じていませんでしたか？</h3>
      <ul style="font-size:0.85rem;color:var(--text-m);line-height:2.4;list-style:none;padding:0;">
        <li>・ 鑑定料が高くて手が出ない</li>
        <li>・ 専門用語が多くて読みこなせない</li>
        <li>・ 鑑定師によって言うことが違う</li>
      </ul>
      <p style="font-size:0.85rem;color:var(--text-m);line-height:2;margin-top:1rem;">
        MOONLOGは、<strong>必要なときに、手頃な価格で、わかりやすく</strong>お届けします。
      </p>
    </div>
  </div>
</section>

<!-- 運営者について -->
<section id="profile" class="sec-mid">
  <div class="inner" style="max-width:720px;">
    <p class="sec-eyebrow">Profile</p>
    <h2 class="sec-title">運営者について</h2>
    <div class="sec-rule"></div>

    <div style="margin-bottom:2.5rem;">
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;margin-bottom:1rem;">
        はじめまして。MOONLOGをつくった、MIDORI です。<br>
        IT系の仕事を長く続けてきた、データと数字が好きな人間です。
      </p>
    </div>

    <div style="margin-bottom:2.5rem;">
      <h3 style="font-family:var(--serif);font-size:1.1rem;font-weight:400;color:var(--text-d);letter-spacing:0.06em;margin-bottom:1.2rem;">わたし自身が、「自分の得意がわからない」人間でした。</h3>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;margin-bottom:1rem;">
        49歳のとき、大学に編入しました。<br>
        50歳を目前に定年を意識し、「これからどう生きるか」を考え始めたのがきっかけです。
      </p>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;margin-bottom:1rem;">
        そして53歳のとき、半年間の休職を経験しました。
      </p>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;">
        仕事を離れて気づいたのは、「もっと努力すれば、いつか自分のことがわかる」と走り続けてきたけれど、<br>
        本当に必要だったのは、<strong>もう持っている自分の傾向を、ちゃんと言葉にして受け取ること</strong>だったということでした。
      </p>
    </div>

    <div style="margin-bottom:2.5rem;">
      <h3 style="font-family:var(--serif);font-size:1.1rem;font-weight:400;color:var(--text-d);letter-spacing:0.06em;margin-bottom:1.2rem;">星読みが、自分を取り戻すきっかけになった。</h3>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;margin-bottom:1rem;">
        もともとIT畑でデータや数字が好きだったわたしにとって、<br>
        「天体配置というデータから、生まれ持った傾向を読む」という星読みのアプローチは、とても腑に落ちるものでした。
      </p>
      <p style="font-size:0.88rem;color:var(--text-m);line-height:2.2;">
        「こうあるべき」という外側の基準ではなく、<br>
        「そもそも自分はどういう人間か」という問いに向き合うための道具として。
      </p>
      <p style="font-family:var(--serif);font-size:0.95rem;color:var(--text-d);line-height:2;margin-top:1.2rem;letter-spacing:0.06em;font-weight:500;">
        もう一度、自分の地図を確かめるために。
      </p>
    </div>

    <div style="background:var(--cream);padding:1.8rem 2rem;border-radius:2px;border:1px solid var(--cream3);">
      <p style="font-size:0.85rem;color:var(--text-m);line-height:2.2;text-align:center;">
        あなたが必要と感じたときに、そっと使ってもらえるサービスを目指しています。
      </p>
    </div>
  </div>
</section>

<!-- フッター -->
<footer>
  <div class="footer-rule"></div>
  <div class="footer-planets">☉ &nbsp; ☽ &nbsp; ☿ &nbsp; ♀ &nbsp; ♂ &nbsp; ♃ &nbsp; ♄</div>
  <div class="footer-logo">MOONLOG</div>
  <p class="footer-copy" style="margin-bottom:0.4rem;">自分を知るための、静かな航海日誌。</p>
  <p class="footer-copy" style="margin-bottom:0.6rem;max-width:560px;margin-left:auto;margin-right:auto;line-height:1.7;">
    本サービスのレポートは、出生時刻の天体配置を計算し、占星術データベースに基づいて自動生成されるものです。プロ占星術師による個別鑑定ではありません。
  </p>
  <div class="footer-links">
    <a href="/blog">ブログ</a>
    <a href="/glossary">用語解説</a>
    <a href="/faq">よくある質問</a>
    <a href="/legal/tokushoho">特定商取引法に基づく表記</a>
    <a href="/legal/privacy">プライバシーポリシー</a>
    <a href="/legal/terms">利用規約</a>
  </div>
  <p class="footer-copy">© 2026 MOONLOG. All rights reserved.</p>
</footer>

<script>
// ── 都市データ（都道府県 → 市区町村 + 座標）──
const CITY_DATA = {
"北海道":[["札幌市",43.0621,141.3544],["函館市",41.7686,140.7289],["旭川市",43.7707,142.3651],["釧路市",42.9849,144.3820],["帯広市",42.9242,143.1966],["北見市",43.8031,143.8933],["小樽市",43.1907,140.9947],["苫小牧市",42.6328,141.6051],["室蘭市",42.3151,140.9735],["千歳市",42.8228,141.6531],["稚内市",45.4161,141.6730],["網走市",44.0183,144.2741],["岩見沢市",43.1961,141.7758],["江別市",43.1036,141.5411]],
"青森県":[["青森市",40.8222,140.7474],["弘前市",40.6031,140.4639],["八戸市",40.5124,141.4882],["五所川原市",40.8075,140.4467],["十和田市",40.6126,141.2066],["むつ市",41.2931,141.1828],["つがる市",40.9078,140.3797]],
"岩手県":[["盛岡市",39.7036,141.1527],["花巻市",39.3889,141.1167],["一関市",38.9342,141.1267],["北上市",39.2819,141.1131],["奥州市",39.1443,141.1386],["宮古市",39.6411,141.9547],["釜石市",39.2764,141.8869]],
"宮城県":[["仙台市",38.2682,140.8694],["石巻市",38.4342,141.3028],["気仙沼市",38.9076,141.5709],["大崎市",38.5764,140.9553],["名取市",38.1714,140.8914],["多賀城市",38.2939,140.9778],["塩竈市",38.3144,141.0219]],
"秋田県":[["秋田市",39.7186,140.1024],["横手市",39.3067,140.5638],["大館市",40.2737,140.5511],["由利本荘市",39.3864,140.0487],["能代市",40.2161,140.0239],["大仙市",39.4564,140.4789]],
"山形県":[["山形市",38.2404,140.3633],["米沢市",37.9222,140.1167],["鶴岡市",38.7344,139.8278],["酒田市",38.9136,139.8367],["天童市",38.3622,140.3783],["東根市",38.4303,140.3961],["新庄市",38.7625,140.3044]],
"福島県":[["福島市",37.7608,140.4748],["郡山市",37.4011,140.3881],["いわき市",37.0508,140.8872],["会津若松市",37.4900,139.9300],["白河市",37.1317,140.2086],["須賀川市",37.2939,140.3767],["南相馬市",37.6428,140.9764]],
"茨城県":[["水戸市",36.3659,140.4712],["日立市",36.5989,140.6517],["つくば市",36.0836,140.0779],["土浦市",36.0822,140.2044],["古河市",36.1936,139.7072],["取手市",35.9017,140.0653],["牛久市",35.9825,140.1486],["ひたちなか市",36.3961,140.5331]],
"栃木県":[["宇都宮市",36.5551,139.8827],["足利市",36.3402,139.4503],["小山市",36.3147,139.8031],["日光市",36.7197,139.6978],["栃木市",36.3811,139.7261],["鹿沼市",36.5628,139.7361],["佐野市",36.3158,139.5961]],
"群馬県":[["前橋市",36.3894,139.0631],["高崎市",36.3219,139.0033],["伊勢崎市",36.3112,139.1972],["太田市",36.2919,139.3758],["桐生市",36.4053,139.3281],["沼田市",36.6461,139.0486],["館林市",36.2411,139.5406]],
"埼玉県":[["さいたま市",35.8617,139.6456],["川越市",35.9251,139.4858],["所沢市",35.7994,139.4694],["春日部市",35.9752,139.7528],["越谷市",35.8881,139.7908],["川口市",35.8078,139.7244],["熊谷市",36.1472,139.3889],["草加市",35.8225,139.8036]],
"千葉県":[["千葉市",35.6074,140.1065],["船橋市",35.6946,139.9828],["松戸市",35.7878,139.9031],["柏市",35.8682,139.9758],["市川市",35.7178,139.9314],["浦安市",35.6536,139.9014],["成田市",35.7769,140.3186],["習志野市",35.6878,140.0219],["八千代市",35.7239,140.1033]],
"東京都":[["千代田区",35.6942,139.7536],["中央区",35.6706,139.7728],["港区",35.6581,139.7514],["新宿区",35.6938,139.7034],["文京区",35.7081,139.7519],["台東区",35.7136,139.7811],["墨田区",35.7106,139.8014],["江東区",35.6720,139.8172],["品川区",35.6094,139.7306],["目黒区",35.6397,139.6983],["大田区",35.5614,139.7175],["世田谷区",35.6465,139.6533],["渋谷区",35.6639,139.6981],["中野区",35.7075,139.6636],["杉並区",35.6997,139.6364],["豊島区",35.7281,139.7189],["北区",35.7528,139.7336],["荒川区",35.7358,139.7828],["板橋区",35.7506,139.7106],["練馬区",35.7358,139.6519],["足立区",35.7751,139.8044],["葛飾区",35.7450,139.8467],["江戸川区",35.7067,139.8681],["八王子市",35.6661,139.3161],["立川市",35.6928,139.4136],["武蔵野市",35.7072,139.5592],["三鷹市",35.6836,139.5606],["青梅市",35.7881,139.2753],["府中市",35.6697,139.4778],["調布市",35.6517,139.5456],["町田市",35.5439,139.4467],["日野市",35.6711,139.3956],["国分寺市",35.6992,139.4647],["西東京市",35.7256,139.5386]],
"神奈川県":[["横浜市",35.4437,139.6380],["川崎市",35.5209,139.7172],["相模原市",35.5533,139.3583],["藤沢市",35.3385,139.4913],["小田原市",35.2656,139.1547],["厚木市",35.4428,139.3573],["横須賀市",35.2811,139.6717],["平塚市",35.3286,139.3522],["鎌倉市",35.3197,139.5467],["茅ヶ崎市",35.3331,139.4031],["大和市",35.4731,139.4628],["海老名市",35.4481,139.3908]],
"新潟県":[["新潟市",37.9161,139.0364],["長岡市",37.4467,138.8508],["上越市",37.1472,138.2356],["柏崎市",37.3706,138.5578],["新発田市",37.9536,139.3239],["三条市",37.6356,138.9622],["燕市",37.6711,138.8814],["十日町市",37.1317,138.7539]],
"富山県":[["富山市",36.6953,137.2113],["高岡市",36.7547,137.0258],["射水市",36.7072,137.0858],["魚津市",36.8311,137.4136],["氷見市",36.8561,136.9872],["砺波市",36.6453,136.9631],["黒部市",36.8653,137.4458]],
"石川県":[["金沢市",36.5944,136.6256],["小松市",36.4056,136.4447],["白山市",36.5131,136.5644],["七尾市",37.0475,136.9625],["加賀市",36.3031,136.3167],["野々市市",36.5253,136.6083],["羽咋市",36.8981,136.7931]],
"福井県":[["福井市",36.0652,136.2217],["敦賀市",35.6481,136.0742],["越前市",35.9014,136.1681],["坂井市",36.1633,136.2281],["鯖江市",35.9567,136.1844],["小浜市",35.4967,135.7467]],
"山梨県":[["甲府市",35.6639,138.5683],["富士吉田市",35.4881,138.7947],["甲斐市",35.6972,138.5261],["笛吹市",35.6492,138.6453],["山梨市",35.6908,138.6886],["甲州市",35.6933,138.7261]],
"長野県":[["長野市",36.6485,138.1947],["松本市",36.2381,137.9717],["上田市",36.4019,138.2492],["飯田市",35.5147,137.8217],["諏訪市",36.0394,138.1128],["塩尻市",36.1156,137.9536],["佐久市",36.2492,138.4728],["安曇野市",36.3061,137.9003],["茅野市",35.9956,138.1589]],
"岐阜県":[["岐阜市",35.4231,136.7608],["大垣市",35.3619,136.6172],["各務原市",35.4006,136.8481],["高山市",36.1461,137.2522],["多治見市",35.3656,137.1317],["関市",35.4983,136.9208],["美濃加茂市",35.4397,137.0072],["土岐市",35.3533,137.1836]],
"静岡県":[["静岡市",34.9769,138.3831],["浜松市",34.7108,137.7261],["沼津市",35.0956,138.8631],["富士市",35.1611,138.6769],["磐田市",34.7183,137.8514],["焼津市",34.8681,138.3228],["藤枝市",34.8681,138.2572],["掛川市",34.7692,138.0133],["御殿場市",35.3083,138.9339]],
"愛知県":[["名古屋市",35.1815,136.9066],["豊橋市",34.7697,137.3914],["岡崎市",34.9481,137.1744],["豊田市",35.0836,137.1564],["一宮市",35.3036,136.8008],["春日井市",35.2478,136.9728],["安城市",34.9592,137.0806],["刈谷市",34.9883,137.0017],["西尾市",34.8669,137.0592],["小牧市",35.2953,136.9119]],
"三重県":[["津市",34.7303,136.5086],["四日市市",34.9644,136.6244],["伊勢市",34.4872,136.7258],["松阪市",34.5769,136.5272],["鈴鹿市",34.8819,136.5836],["名張市",34.6281,136.1086],["伊賀市",34.7669,136.1314]],
"滋賀県":[["大津市",35.0044,135.8686],["草津市",35.0147,135.9608],["彦根市",35.2753,136.2514],["長浜市",35.3836,136.2703],["近江八幡市",35.1278,136.0983],["守山市",35.0617,135.9942],["栗東市",35.0131,135.9947]],
"京都府":[["京都市",35.0116,135.7681],["宇治市",34.8942,135.7994],["長岡京市",34.9278,135.6906],["亀岡市",35.0094,135.5756],["舞鶴市",35.4728,135.3933],["福知山市",35.2981,135.1214],["城陽市",34.8886,135.7778]],
"大阪府":[["大阪市",34.6937,135.5023],["堺市",34.5733,135.4830],["東大阪市",34.6794,135.6019],["枚方市",34.8133,135.6536],["豊中市",34.7831,135.4706],["吹田市",34.7606,135.5153],["高槻市",34.8494,135.6172],["茨木市",34.8167,135.5644],["八尾市",34.6264,135.6003],["寝屋川市",34.7683,135.6353]],
"兵庫県":[["神戸市",34.6901,135.1956],["姫路市",34.8153,134.6861],["尼崎市",34.7336,135.4069],["西宮市",34.7386,135.3431],["宝塚市",34.7986,135.3592],["明石市",34.6453,134.9972],["加古川市",34.7572,134.8372],["三田市",34.8908,135.2244],["伊丹市",34.7783,135.4011]],
"奈良県":[["奈良市",34.6851,135.8050],["橿原市",34.5081,135.7956],["生駒市",34.6958,135.6958],["大和高田市",34.5236,135.7394],["大和郡山市",34.6469,135.7833],["天理市",34.5961,135.8381],["桜井市",34.5181,135.8447]],
"和歌山県":[["和歌山市",34.2261,135.1675],["田辺市",33.7333,135.3725],["橋本市",34.3197,135.5972],["有田市",34.0703,135.1367],["海南市",34.1681,135.2172],["御坊市",33.8919,135.1594]],
"鳥取県":[["鳥取市",35.5011,134.2353],["米子市",35.4281,133.3308],["倉吉市",35.4297,133.8253],["境港市",35.5428,133.2281]],
"島根県":[["松江市",35.4681,133.0508],["出雲市",35.3672,132.7550],["浜田市",34.8994,132.0817],["益田市",34.6742,131.8444],["安来市",35.4339,133.2586]],
"岡山県":[["岡山市",34.6617,133.9344],["倉敷市",34.5906,133.7736],["津山市",35.0681,133.9997],["総社市",34.6775,133.7456],["笠岡市",34.5003,133.5078],["玉野市",34.4883,133.9472],["備前市",34.7256,134.1806]],
"広島県":[["広島市",34.3853,132.4553],["呉市",34.2492,132.5658],["福山市",34.4858,133.3625],["東広島市",34.4269,132.7433],["尾道市",34.4083,133.2089],["三原市",34.3978,133.0814],["廿日市市",34.3461,132.3339]],
"山口県":[["下関市",33.9519,130.9428],["山口市",34.1861,131.4706],["宇部市",33.9522,131.2472],["周南市",34.0553,131.8061],["防府市",34.0517,131.5622],["岩国市",34.1661,132.2239],["萩市",34.4083,131.3997]],
"徳島県":[["徳島市",34.0658,134.5594],["阿南市",33.9208,134.6617],["鳴門市",34.1767,134.6094],["吉野川市",34.0703,134.3708],["阿波市",34.0978,134.1719]],
"香川県":[["高松市",34.3403,134.0433],["丸亀市",34.2883,133.7969],["観音寺市",34.1267,133.6606],["坂出市",34.3189,133.8608],["さぬき市",34.3256,134.1783],["三豊市",34.1903,133.7206]],
"愛媛県":[["松山市",33.8392,132.7658],["今治市",34.0661,132.9981],["新居浜市",33.9608,133.2836],["西条市",33.9225,133.1814],["宇和島市",33.2253,132.5597],["大洲市",33.5031,132.5431]],
"高知県":[["高知市",33.5597,133.5311],["南国市",33.5736,133.6461],["四万十市",32.9936,132.9347],["安芸市",33.5022,133.9075],["須崎市",33.3983,133.2814]],
"福岡県":[["福岡市",33.5904,130.4017],["北九州市",33.8834,130.8751],["久留米市",33.3189,130.5089],["飯塚市",33.6461,130.6906],["春日市",33.5339,130.4708],["大野城市",33.5361,130.4786],["筑紫野市",33.5244,130.5144],["太宰府市",33.5153,130.5242],["糸島市",33.5567,130.2006]],
"佐賀県":[["佐賀市",33.2636,130.3008],["唐津市",33.4486,129.9703],["鳥栖市",33.3786,130.5036],["伊万里市",33.2664,129.8797],["武雄市",33.1928,130.0156]],
"長崎県":[["長崎市",32.7503,129.8778],["佐世保市",33.1739,129.7153],["諫早市",32.8428,130.0592],["大村市",32.9183,129.9578],["島原市",32.7878,130.3697]],
"熊本県":[["熊本市",32.8032,130.7079],["八代市",32.5069,130.6006],["天草市",32.4597,130.1981],["玉名市",32.9281,130.5558],["荒尾市",32.9981,130.4286],["山鹿市",33.0147,130.6914]],
"大分県":[["大分市",33.2382,131.6128],["別府市",33.2844,131.4906],["中津市",33.5983,131.1886],["日田市",33.3219,130.9414],["佐伯市",32.9597,131.9006],["宇佐市",33.5272,131.3503]],
"宮崎県":[["宮崎市",31.9077,131.4202],["都城市",31.7208,131.0647],["延岡市",32.5817,131.6617],["日向市",32.4239,131.6256],["日南市",31.5986,131.3731]],
"鹿児島県":[["鹿児島市",31.5969,130.5571],["霧島市",31.7408,130.7644],["薩摩川内市",31.8092,130.3022],["鹿屋市",31.3794,130.8519],["指宿市",31.2514,130.6375],["出水市",32.0872,130.3594]],
"沖縄県":[["那覇市",26.2124,127.6809],["沖縄市",26.3344,127.8044],["宜野湾市",26.2817,127.7781],["浦添市",26.2461,127.7197],["うるま市",26.3753,127.8578],["名護市",26.5917,127.9778],["石垣市",24.3368,124.1564],["宮古島市",24.8056,125.2814]]
};

function updateCities(pref) {
  const citySelect = document.getElementById('city_select');
  citySelect.innerHTML = '<option value="">市区町村を選択</option>';
  if (!pref || !CITY_DATA[pref]) return;
  CITY_DATA[pref].forEach(c => {
    const opt = document.createElement('option');
    opt.value = c[0];
    opt.dataset.lat = c[1];
    opt.dataset.lng = c[2];
    opt.textContent = c[0];
    citySelect.appendChild(opt);
  });
  citySelect.selectedIndex = 1;
  updateLatLng(citySelect);
}

function updateLatLng(sel) {
  const opt = sel.options[sel.selectedIndex];
  if (opt && opt.dataset.lat) {
    document.getElementById('lat_field').value = opt.dataset.lat;
    document.getElementById('lng_field').value = opt.dataset.lng;
  }
}

// 初期化：プルダウンは未選択のまま（ユーザーが選ぶ）
window.addEventListener('DOMContentLoaded', () => {

  // SR年セレクターを動的生成（今年-1 〜 今年+3）
  const srYearSel = document.getElementById('sr_year');
  const currentYear = new Date().getFullYear();
  for (let y = currentYear - 1; y <= currentYear + 3; y++) {
    const opt = document.createElement('option');
    opt.value = y;
    opt.textContent = y + '年';
    if (y === currentYear) opt.selected = true;
    srYearSel.appendChild(opt);
  }
});

{
const _btnPptx = document.getElementById('btn-pptx');
if (_btnPptx) _btnPptx.addEventListener('click', async () => {
  const form   = document.getElementById('form');
  const btn    = document.getElementById('btn-pptx');
  const status = document.getElementById('status');

  if (!form.reportValidity()) return;

  btn.disabled = true;
  status.className = 'status-wait';
  status.innerHTML = '星の配置を計算しています<span class="loading-dots"></span><br><small style="opacity:0.6">（通常10〜30秒ほどかかります）</small>';

  const data = Object.fromEntries(new FormData(form));

  try {
    const res = await fetch('/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.error || 'エラーが発生しました');
    }
    const blob = await res.blob();
    const name = data.name || '星読みレポート';
    const url  = URL.createObjectURL(blob);
    const a    = document.createElement('a');
    a.href = url; a.download = `${name}_星読みレポート.pptx`; a.click();
    URL.revokeObjectURL(url);
    status.className = 'status-ok';
    status.textContent = 'PPTXが生成されました。ダウンロードをご確認ください。';
  } catch (err) {
    status.className = 'status-err';
    status.textContent = err.message;
  } finally {
    btn.disabled = false;
  }
});
}

// === 有料ボタン押下時の必須チェック v3 (2026-05-23) ===
console.log('[moonlog] paid-button validator v3 loaded');
(function(){
  const PAID_IDS = ['btn-natal', 'btn-sr', 'btn-fr'];
  const emailField = document.getElementById('paid_email');
  const errorBox   = document.getElementById('paid_email_error');
  if (!emailField || !errorBox) { console.warn('[moonlog] emailField or errorBox not found'); return; }

  function showErr(msgs){
    // msgs は配列。1件なら通常表示、複数ならリスト表示
    const arr = Array.isArray(msgs) ? msgs : [msgs];
    if (arr.length === 1) {
      errorBox.innerHTML = '⚠ ' + arr[0];
    } else {
      let html = '<div style="font-weight:700;margin-bottom:6px;">⚠ 入力に不足があります：</div><ul style="margin:0;padding-left:22px;font-weight:500;">';
      arr.forEach(function(m){ html += '<li>' + m + '</li>'; });
      html += '</ul>';
      errorBox.innerHTML = html;
    }
    errorBox.style.display = 'block';
    emailField.style.borderColor = '#c0392b';
    errorBox.scrollIntoView({behavior:'smooth', block:'center'});
  }
  function clearErr(){
    errorBox.style.display = 'none';
    errorBox.textContent = '';
    emailField.style.borderColor = '#d5c5a3';
  }

  function validatePaid(){
    const errs = [];
    const name  = (document.querySelector('input[name="name"]')?.value || '').trim();
    const year  = (document.querySelector('input[name="year"]')?.value || '').trim();
    const month = (document.querySelector('input[name="month"]')?.value || '').trim();
    const day   = (document.querySelector('input[name="day"]')?.value || '').trim();
    const pref  = (document.getElementById('pref_select')?.value || '').trim();
    const city  = (document.querySelector('select[name="city"]')?.value || '').trim();
    const mail  = (emailField.value || '').trim();
    if (!name)  errs.push('お名前を入力してください。');
    if (!year || !month || !day) errs.push('生年月日を入力してください。');
    if (!pref || !city) errs.push('出生地（都道府県・市区町村）を選択してください。');
    if (!mail)  errs.push('PDF送付先のメールアドレスを入力してください。');
    else if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(mail)) errs.push('メールアドレスの形式が正しくないようです。');
    return errs;  // 空配列ならOK
  }

  // 入力すると自動でエラー消去
  ['paid_email'].forEach(function(id){
    const el = document.getElementById(id);
    if (el) el.addEventListener('input', clearErr);
  });

  // 各有料ボタンに直接 click イベント（最確実）
  PAID_IDS.forEach(function(id){
    const btn = document.getElementById(id);
    if (!btn) { console.warn('[moonlog] button not found:', id); return; }
    console.log('[moonlog] attaching click handler to:', id);
    btn.addEventListener('click', function(ev){
      console.log('[moonlog] paid button clicked:', id);
      const errs = validatePaid();
      if (errs.length > 0) {
        console.log('[moonlog] validation errors:', errs);
        ev.preventDefault();
        ev.stopPropagation();
        ev.stopImmediatePropagation();
        showErr(errs);
        return false;
      }
      console.log('[moonlog] validation passed');
      clearErr();
    }, true); // capture phase
  });

  // submit イベントも保険として捕捉（Enterキー対策）
  document.querySelectorAll('form').forEach(function(form){
    form.addEventListener('submit', function(ev){
      const submitter = ev.submitter;
      if (!submitter || !PAID_IDS.includes(submitter.id)) return;
      const errs = validatePaid();
      if (errs.length > 0) {
        ev.preventDefault();
        ev.stopPropagation();
        showErr(errs);
        return false;
      }
    }, true);
  });
})();
</script>
</body>
</html>"""

# ============================================================
# ルーティング
# ============================================================

@app.route("/robots.txt")
def robots_txt():
    from flask import Response
    content = """# MOONLOG robots.txt
# AI crawlers and scrapers are not permitted

Sitemap: https://moonlog.jp/sitemap.xml

User-agent: GPTBot
Disallow: /

User-agent: ChatGPT-User
Disallow: /

User-agent: CCBot
Disallow: /

User-agent: anthropic-ai
Disallow: /

User-agent: Claude-Web
Disallow: /

User-agent: Googlebot
Disallow: /generate
Disallow: /preview
Disallow: /solar_return
Disallow: /lifecycle
Disallow: /my_reading
Disallow: /hayate_reading
Disallow: /fuuki_reading

User-agent: *
Disallow: /generate
Disallow: /preview
Disallow: /solar_return
Disallow: /lifecycle
Disallow: /my_reading
Disallow: /hayate_reading
Disallow: /fuuki_reading
"""
    return Response(content, mimetype="text/plain")


@app.route("/")
def index():
    # 環境変数 SHOW_PAID_PRODUCTS=1 で有料商品カードを表示
    # 未設定または "0" の場合は「Coming Soon」モード（ソフトローンチ用）
    show_paid = os.environ.get("SHOW_PAID_PRODUCTS", "0") == "1"
    return render_template_string(
        HTML, show_paid=show_paid,
        release_date_jp=RELEASE_DATE_JP,
        release_date_dot=RELEASE_DATE_DOT,
        release_date_md=RELEASE_DATE_MD,
        coupon_end_jp=COUPON_END_JP,
        coupon_range=COUPON_RANGE,
    )


# ============================================================
# タイプ診断（月星座 → 12タイプ）
# ============================================================

@app.route("/type")
def type_input():
    from flask import Response
    return Response(moonlog_types.render_input_page(),
                    mimetype="text/html; charset=utf-8")


@app.route("/type/result", methods=["POST"])
def type_result():
    from flask import Response
    data = request.form
    city = str(data.get("city", "東京")).strip() or "東京"
    lat = lng = None
    bd = str(data.get("birthdate", "")).strip()
    try:
        if bd:  # 単独タイプ診断フォーム（YYYY-MM-DD）
            y, mo, d = [int(x) for x in bd.split("-")]
            bt = str(data.get("birthtime", "")).strip()
            if bt:
                h, mi = [int(x) for x in bt.split(":")[:2]]
            else:
                h, mi = 12, 0
        else:  # トップページの共通フォーム（year/month/day...）
            y  = int(data["year"]); mo = int(data["month"]); d = int(data["day"])
            h  = int(data.get("hour", 12)); mi = int(data.get("minute", 0))
            if data.get("lat"):
                lat = float(data["lat"])
            if data.get("lng"):
                lng = float(data["lng"])
    except Exception:
        return Response(moonlog_types._err_page("生年月日を正しく入力してください。"),
                        mimetype="text/html; charset=utf-8", status=400)
    try:
        moon_key, sun_key = moonlog_types.compute_type(
            y, mo, d, h, mi, city, lat=lat, lng=lng)
    except Exception:
        import traceback; traceback.print_exc()
        return Response(moonlog_types._err_page(
            "計算中にエラーが発生しました。出生地を変えて、もう一度お試しください。"),
            mimetype="text/html; charset=utf-8", status=500)

    # 体験版（/preview）へ引き継ぐための birth_data
    name = str(data.get("name", "")).strip() or "あなた"
    birth_data = {
        "name": name, "year": y, "month": mo, "day": d,
        "hour": h, "minute": mi, "city": city,
    }
    if lat is not None: birth_data["lat"] = lat
    if lng is not None: birth_data["lng"] = lng

    return Response(
        moonlog_types.render_result_page(moon_key, sun_key, birth_data=birth_data),
        mimetype="text/html; charset=utf-8")


# ============================================================
# PDF生成（Playwright Chromium ヘッドレス）
# ============================================================

def html_to_pdf_bytes(html_str):
    """HTML文字列をPDFバイト列に変換する。
    優先: Playwright(Chromium)。失敗時は WeasyPrint へフォールバック。
    本番環境(Render)では WeasyPrint を使うのが想定。
    """
    # Playwright を試す（ローカル開発で使用想定）
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            try:
                page = browser.new_page()
                import base64
                b64 = base64.b64encode(html_str.encode("utf-8")).decode("ascii")
                page.goto(f"data:text/html;base64,{b64}", wait_until="networkidle", timeout=30000)
                page.wait_for_timeout(500)
                pdf_bytes = page.pdf(
                    format="A4",
                    margin={"top":"14mm","bottom":"14mm","left":"12mm","right":"12mm"},
                    print_background=True,
                    prefer_css_page_size=False,
                )
            finally:
                browser.close()
        return pdf_bytes
    except Exception as e:
        # Playwright が使えない環境 (本番Render) では WeasyPrint へフォールバック
        print(f"[html_to_pdf_bytes] Playwright失敗 → WeasyPrintへ: {e}")
        from weasyprint import HTML
        return HTML(string=html_str).write_pdf()


FEEDBACK_FORM_URL = os.environ.get("FEEDBACK_FORM_URL", "https://forms.gle/P82aWvS61fpN2X1J9")
COUPON_CODE = os.environ.get("COUPON_CODE", "EARLYBIRD500")

# ============================================================
# 日付定数（一括変更用）— 環境変数で上書き可能
# ============================================================
RELEASE_DATE_JP  = os.environ.get("RELEASE_DATE_JP",  "2026年6月1日")     # 「2026年6月1日」表記
RELEASE_DATE_DOT = os.environ.get("RELEASE_DATE_DOT", "2026.6.1")          # 「2026.6.1」表記
RELEASE_DATE_MD  = os.environ.get("RELEASE_DATE_MD",  "6/1")               # 「6/1」短縮表記
COUPON_END_JP    = os.environ.get("COUPON_END_JP",    "7月31日")           # クーポン期限「7月31日」
COUPON_RANGE     = os.environ.get("COUPON_RANGE",     "6/1〜7/31")         # クーポン期間「6/1〜7/31」

# ============================================================
# SMTP メール送信（PDF添付）
# ============================================================
SMTP_HOST = os.environ.get("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.environ.get("SMTP_PORT", "587"))
SMTP_USER = os.environ.get("SMTP_USER", "")
SMTP_PASS = os.environ.get("SMTP_PASS", "")
SMTP_FROM = os.environ.get("SMTP_FROM", "info@moonlog.jp")
SMTP_FROM_NAME = os.environ.get("SMTP_FROM_NAME", "moonlog")


def send_pdf_email(to_email, subject, body_text, pdf_bytes, pdf_filename):
    """SMTP 経由で PDF を添付してメール送信"""
    if not (SMTP_USER and SMTP_PASS):
        print("[send_pdf_email] SMTP未設定 — スキップ")
        return False
    import smtplib
    from email.message import EmailMessage
    msg = EmailMessage()
    msg["Subject"] = subject
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_FROM}>"
    msg["To"] = to_email
    msg.set_content(body_text)
    msg.add_attachment(pdf_bytes, maintype="application", subtype="pdf", filename=pdf_filename)
    try:
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=20) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        print(f"[send_pdf_email] ✅ sent to {to_email}")
        return True
    except Exception as e:
        import traceback; traceback.print_exc()
        print(f"[send_pdf_email] ❌ {e}")
        return False


# ============================================================
# Stripe Checkout
# ============================================================
STRIPE_PUBLISHABLE_KEY = os.environ.get("STRIPE_PUBLISHABLE_KEY", "")
STRIPE_SECRET_KEY = os.environ.get("STRIPE_SECRET_KEY", "")
STRIPE_PRICE_NATAL = os.environ.get("STRIPE_PRICE_NATAL", "price_1TXDOyAmhBJUjslZfONNA15h")
SITE_URL = os.environ.get("SITE_URL", "https://moonlog.jp")

try:
    import stripe
    if STRIPE_SECRET_KEY:
        stripe.api_key = STRIPE_SECRET_KEY
    _stripe_ready = bool(STRIPE_SECRET_KEY)
except ImportError:
    stripe = None
    _stripe_ready = False


@app.route("/checkout/natal", methods=["POST"])
def checkout_natal():
    """出生チャート購入: Stripe Checkout セッション作成 → リダイレクト"""
    if not _stripe_ready:
        return "<p>決済機能の準備中です。後ほどお試しください。</p>", 503
    data = request.form
    try:
        meta = {
            "product": "natal",
            "name":   str(data.get("name", ""))[:80],
            "year":   str(int(data["year"])),
            "month":  str(int(data["month"])),
            "day":    str(int(data["day"])),
            "hour":   str(int(data.get("hour", 12))),
            "minute": str(int(data.get("minute", 0))),
            "city":   str(data.get("city", "東京"))[:60],
            "lat":    str(float(data.get("lat") or 35.6762)),
            "lng":    str(float(data.get("lng") or 139.6503)),
        }
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400

    # PDF送付先メアド取得（フォームから）
    paid_email = str(data.get("email", "")).strip()
    # 簡易バリデーション
    import re as _re
    if not paid_email or not _re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", paid_email):
        # JS側で防げなかった場合のフォールバック。ブラウザ戻るで入力データを保持
        return """<!doctype html><html lang="ja"><head><meta charset="utf-8">
<title>moonlog | メールアドレスを入力してください</title>
<style>
body{font-family:-apple-system,'Hiragino Kaku Gothic ProN',sans-serif;background:#F5F2EC;color:#3a2818;margin:0;padding:40px 20px;display:flex;align-items:center;justify-content:center;min-height:100vh;}
.box{background:#fff;max-width:480px;padding:32px 28px;border-radius:12px;box-shadow:0 8px 24px rgba(0,0,0,0.08);text-align:center;}
.icon{font-size:48px;margin-bottom:12px;}
h1{font-size:1.15rem;color:#5A3818;margin:0 0 16px;}
p{font-size:0.95rem;line-height:1.7;color:#8c7858;margin:0 0 24px;}
.btn{display:inline-block;background:#1a2740;color:#fff;padding:12px 32px;border-radius:6px;text-decoration:none;font-weight:600;font-size:0.95rem;}
.btn:hover{background:#2a3a55;}
</style></head><body>
<div class="box">
<div class="icon">📧</div>
<h1>PDF送付先のメールアドレスが未入力です</h1>
<p>有料レポートの購入には、PDFをお届けするメールアドレスが必要です。<br>戻ってメールアドレスをご入力ください。</p>
<a href="javascript:history.back()" class="btn">← 入力画面に戻る</a>
</div></body></html>""", 400

    # PDF送付先メアドはmetadataにのみ保存（Stripe Checkout画面には引き継がない）
    # 理由：customer_email を渡すとStripe Linkが自動ログインを要求してUXが悪化するため
    meta["paid_email"] = paid_email

    try:
        checkout_kwargs = dict(
            mode="payment",
            line_items=[{"price": STRIPE_PRICE_NATAL, "quantity": 1}],
            payment_method_types=["card"],
            allow_promotion_codes=True,
            success_url=f"{SITE_URL}/checkout/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{SITE_URL}/#form-section",
            metadata=meta,
            locale="ja",
            # customer_email は意図的に渡さない（Link自動ログイン回避のため）
        )
        session = stripe.checkout.Session.create(**checkout_kwargs)
        return redirect(session.url, code=303)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>決済セッションの作成に失敗しました。時間をおいてお試しください。</p>", 500


@app.route("/checkout/success")
def checkout_success():
    """決済完了後: メタデータから出生情報を取り出して有料版レポート表示"""
    from flask import Response
    sid = request.args.get("session_id", "")
    if not sid or not _stripe_ready:
        return redirect("/", code=302)
    try:
        sess = stripe.checkout.Session.retrieve(sid)
        if sess.payment_status != "paid":
            return "<p>決済が完了していません。お支払い後にこのページが表示されます。</p>", 402
        m = sess.metadata.to_dict_recursive() if hasattr(sess.metadata, "to_dict_recursive") else (sess.metadata.to_dict() if hasattr(sess.metadata, "to_dict") else dict(sess.metadata or {}))
        if m.get("product") != "natal":
            return redirect("/", code=302)
        name   = m.get("name") or "あなた"
        year   = int(m["year"]); month = int(m["month"]); day = int(m["day"])
        hour   = int(m["hour"]); minute = int(m["minute"])
        city   = m.get("city", "東京")
        lat    = float(m.get("lat", 35.6762))
        lng    = float(m.get("lng", 139.6503))
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>購入情報の取得に失敗しました。お手数ですが info@moonlog.jp までお問い合わせください。</p>", 500

    try:
        # 有料フル版（light=False）
        html = generate_html_report(
            name, year, month, day, hour, minute, city,
            lat=lat, lng=lng, tz_str="Asia/Tokyo", light=False
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>レポートの生成中にエラーが発生しました。お手数ですが info@moonlog.jp までお問い合わせください。</p>", 500

    # メール送信（非同期・1回限り）
    # PDF送付先は metadata["paid_email"]（moonlogフォームで入力されたもの）を優先
    # フォールバックとして Stripe決済時のメアドも参照
    customer_email = ""
    try:
        meta_obj = sess.metadata if hasattr(sess, "metadata") else None
        if meta_obj and meta_obj.get("paid_email"):
            customer_email = meta_obj.get("paid_email")
        elif sess.customer_details and sess.customer_details.email:
            customer_email = sess.customer_details.email
    except Exception:
        pass

    if customer_email and not (sess.metadata.get("emailed") == "1" if hasattr(sess.metadata, "get") else False):
        def _send_async():
            try:
                pdf_bytes = html_to_pdf_bytes(html)
                ok = send_pdf_email(
                    to_email=customer_email,
                    subject=f"【moonlog】{name}さんの出生チャート診断レポート",
                    body_text=(
                        f"{name}さま\n\n"
                        f"このたびはmoonlogをご利用いただきありがとうございます。\n"
                        f"出生チャート診断レポート（フル版）のPDFを添付しました。\n\n"
                        f"ご感想やお気づきの点がございましたら、\n"
                        f"ぜひフィードバックフォームよりお知らせください：\n"
                        f"{FEEDBACK_FORM_URL}\n\n"
                        f"あなたの星の地図が、これからの日々の道しるべになりますように。\n\n"
                        f"moonlog ｜ 自分という地図\n"
                        f"https://moonlog.jp\n"
                    ),
                    pdf_bytes=pdf_bytes,
                    pdf_filename=f"moonlog_natal_{name}.pdf",
                )
                # 二重送信防止のためメタデータに記録
                try:
                    stripe.checkout.Session.modify(sid, metadata={**m, "emailed": "1" if ok else "0"})
                except Exception:
                    pass
            except Exception as e:
                import traceback; traceback.print_exc()
                print(f"[checkout_success] メール送信失敗: {e}")
        threading.Thread(target=_send_async, daemon=True).start()

    # 購入完了バナーを冒頭に挿入
    email_note = f"<br><small style='font-size:.85em;opacity:.9'>📧 PDFを {customer_email} にお送りしました（数分以内に届きます）</small>" if customer_email else ""
    banner = (
        '<div style="background:#2C3E6B;color:#fff;padding:18px 20px;text-align:center;'
        'font-family:\'Hiragino Mincho ProN\',serif;letter-spacing:.05em;">'
        f'🌙 ご購入ありがとうございました — 出生チャート診断レポート（フル版）{email_note}</div>'
    )
    if "<body" in html:
        i = html.find(">", html.find("<body")) + 1
        html = html[:i] + banner + html[i:]
    else:
        html = banner + html

    return Response(html, mimetype="text/html; charset=utf-8")

def _free_cta_footer(name, year, month, day, hour, minute, city, lat, lng):
    """出生チャート 無料体験版の末尾に挿入するCTA：フィードバック + クーポン"""
    return f"""
<div style="background:#FBF8F2;padding:48px 24px;border-top:2px solid #B89858;margin-top:48px;">
  <div style="max-width:680px;margin:0 auto;">
    <div style="background:rgba(184,152,88,.08);border:1px dashed #B89858;border-radius:4px;padding:24px;margin-bottom:24px;">
      <h3 style="font-family:'Hiragino Mincho ProN',serif;color:#5A3818;margin:0 0 8px;font-size:1.2rem;text-align:center;">🌹 もう少しだけ、お時間をいただけますか？</h3>
      <p style="color:#1C1A2E;line-height:1.85;margin:8px 0;font-size:.95rem;">
        読んでみての感想・違和感・「これは私だ」と感じた箇所、ぜひ教えてください。<br>
        moonlog はまだ磨いている最中で、あなたの声が、リリース時の品質を作ります。
      </p>
      <p style="text-align:center;margin:16px 0 8px;">
        <a href="{FEEDBACK_FORM_URL}" target="_blank" rel="noopener" style="display:inline-block;background:#B89858;color:#fff;text-decoration:none;padding:12px 28px;border-radius:4px;font-size:.95rem;letter-spacing:.04em;">
          ✦ 感想を送る（1分で完了）
        </a>
      </p>
      <p style="text-align:center;color:#6B607A;font-size:.85rem;margin:8px 0 0;">
        フィードバックをくれた方には、{RELEASE_DATE_JP}リリース時に使える<br>
        <strong style="color:#5A3818;font-size:1.05rem;">¥500 OFF クーポン</strong> をお届けします<br>
        <small>（出生チャート/年間星読み/3分野レポート ¥980 → ¥480）</small><br>
        <small style="color:#9A8870;">※ クーポンコードは、フォーム送信後の完了画面に表示されます。</small>
      </p>
    </div>

    <p style="text-align:center;color:#9A8870;font-size:.82rem;line-height:1.7;margin:0;">
      ※ クーポンは{COUPON_RANGE}の期間限定です。
    </p>
  </div>
</div>
"""

def _esc(s):
    import html as h
    return h.escape(str(s))


@app.route("/preview", methods=["POST"])
def preview():
    from flask import Response
    data = request.form
    try:
        name   = str(data.get("name", "")).strip() or "あなた"
        year   = int(data["year"])
        month  = int(data["month"])
        day    = int(data["day"])
        hour   = int(data.get("hour", 12))
        minute = int(data.get("minute", 0))
        city   = str(data.get("city", "新潟市")).strip()
        lat    = float(data.get("lat") or 37.9161)
        lng    = float(data.get("lng") or 139.0364)
        tz     = "Asia/Tokyo"
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400

    try:
        # 出生チャート 無料体験版（太陽・月のみ）
        html = generate_html_report(
            name, year, month, day, hour, minute, city,
            lat=lat, lng=lng, tz_str=tz, light=True
        )
        # CTAフッターを末尾に追加
        cta = _free_cta_footer(name, year, month, day, hour, minute, city, lat, lng)
        if "</body>" in html:
            html = html.replace("</body>", cta + "</body>")
        else:
            html = html + cta
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>エラーが発生しました。時間をおいてお試しください。</p>", 500

    return Response(html, mimetype="text/html; charset=utf-8")


@app.route("/generate", methods=["POST"])
def generate():
    from flask import Response
    data = request.get_json()
    try:
        name   = str(data.get("name", "")).strip() or "あなた"
        year   = int(data["year"])
        month  = int(data["month"])
        day    = int(data["day"])
        hour   = int(data.get("hour", 12))
        minute = int(data.get("minute", 0))
        city   = str(data.get("city", "新潟市")).strip()
        lat    = float(data.get("lat") or 37.9161)
        lng    = float(data.get("lng") or 139.0364)
        tz     = "Asia/Tokyo"
    except (KeyError, ValueError) as e:
        return jsonify({"error": "入力値が正しくありません。入力内容をご確認ください。"}), 400

    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = generate_report(
                name, year, month, day, hour, minute, city,
                lat=lat, lng=lng, tz_str=tz, output_dir=tmpdir
            )
            with open(output_path, "rb") as f:
                pptx_bytes = f.read()
    except Exception as e:
        import traceback; traceback.print_exc()
        return jsonify({"error": "レポート生成中にエラーが発生しました。時間をおいてお試しください。"}), 500

    return Response(
        pptx_bytes,
        mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={"Content-Disposition": f"attachment; filename=\"report.pptx\"; filename*=UTF-8''{__import__('urllib.parse',fromlist=['quote']).quote(name + '_星読みレポート.pptx')}"}
    )


@app.route("/solar_return", methods=["POST"])
def solar_return():
    from flask import Response
    data = request.form
    try:
        name     = str(data.get("name", "")).strip() or "あなた"
        year     = int(data["year"])
        month    = int(data["month"])
        day      = int(data["day"])
        hour     = int(data.get("hour", 12))
        minute   = int(data.get("minute", 0))
        city     = str(data.get("city", "新潟市")).strip()
        lat      = float(data.get("lat") or 37.9161)
        lng      = float(data.get("lng") or 139.0364)
        tz       = "Asia/Tokyo"
        sr_year_raw = data.get("sr_year", "")
        sr_year  = int(sr_year_raw) if sr_year_raw.strip().isdigit() else None
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400

    try:
        html = generate_solar_return_html(
            name, year, month, day, hour, minute, city,
            lat=lat, lng=lng, tz_str=tz,
            target_year=sr_year
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>星読みの計算中にエラーが発生しました。時間をおいてお試しください。</p>", 500

    return Response(html, mimetype="text/html; charset=utf-8")


@app.route("/field_report", methods=["POST"])
def field_report():
    """3分野レポート（仕事・お金・恋愛）"""
    from flask import Response
    data = request.form
    try:
        name   = str(data.get("name", "")).strip() or "あなた"
        year   = int(data["year"])
        month  = int(data["month"])
        day    = int(data["day"])
        hour   = int(data.get("hour", 12))
        minute = int(data.get("minute", 0))
        city   = str(data.get("city", "新潟市")).strip()
        lat    = float(data.get("lat") or 37.9161)
        lng    = float(data.get("lng") or 139.0364)
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400
    try:
        html = generate_field_report_html(
            name, year, month, day, hour, minute, city,
            lat=lat, lng=lng, tz_str="Asia/Tokyo",
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>3分野レポートの計算中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    return Response(html, mimetype="text/html; charset=utf-8")


@app.route("/sample/field_report")
def sample_field_report():
    """3分野レポート サンプル"""
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_field_report_html(
            s["name"], s["year"], s["month"], s["day"],
            s["hour"], s["minute"], s["city"],
            lat=s["lat"], lng=s["lng"], sample=True
        )
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>サンプル生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    return Response(html, mimetype="text/html; charset=utf-8")


@app.route("/lifecycle", methods=["POST"])
def lifecycle():
    from flask import Response
    data = request.form
    try:
        name  = str(data.get("name","")).strip() or "あなた"
        year  = int(data["year"])
        month = int(data["month"])
        day   = int(data["day"])
        city  = str(data.get("city","")).strip()
        lat   = float(data.get("lat") or 35.6762)
        lng   = float(data.get("lng") or 139.6503)
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400
    try:
        html = generate_lifecycle_html(name, year, month, day, city, lat=lat, lng=lng)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>ライフサイクルの計算中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    return Response(html, mimetype="text/html; charset=utf-8")


# ============================================================
# サンプルレポート（チラ見せ用）
# ============================================================
# 固定のダミーデータでレポートを生成し、購入前のプレビューを提供
SAMPLE_DATA = {
    "name":  "星野 空",
    "year":  1985, "month": 4, "day": 15,
    "hour":  14,  "minute": 30,
    "city":  "東京",
    "lat":   35.6762, "lng": 139.6503,
}

@app.route("/sample/natal")
def sample_natal():
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_html_report(s["name"], s["year"], s["month"], s["day"],
                                     s["hour"], s["minute"], s["city"],
                                     lat=s["lat"], lng=s["lng"], sample=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>サンプル生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    return Response(html, mimetype="text/html; charset=utf-8")

@app.route("/sample/sr")
def sample_sr():
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_solar_return_html(s["name"], s["year"], s["month"], s["day"],
                                           s["hour"], s["minute"], s["city"],
                                           lat=s["lat"], lng=s["lng"],
                                           tz_str="Asia/Tokyo", target_year=2026, sample=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>サンプル生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    return Response(html, mimetype="text/html; charset=utf-8")

# ── PDFダウンロード（フォーム送信から）──
@app.route("/pdf/natal", methods=["POST"])
def pdf_natal():
    from flask import Response
    data = request.form
    try:
        name   = str(data.get("name", "")).strip() or "あなた"
        year   = int(data["year"]); month = int(data["month"]); day = int(data["day"])
        hour   = int(data.get("hour", 12)); minute = int(data.get("minute", 0))
        city   = str(data.get("city", "新潟市")).strip()
        lat    = float(data.get("lat") or 37.9161)
        lng    = float(data.get("lng") or 139.0364)
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400
    try:
        html = generate_html_report(name, year, month, day, hour, minute, city,
                                     lat=lat, lng=lng, tz_str="Asia/Tokyo")
        pdf  = html_to_pdf_bytes(html)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>PDF生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    from urllib.parse import quote
    fname = f"{name}_出生チャート.pdf"
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"report.pdf\"; filename*=UTF-8''{quote(fname)}"})


@app.route("/pdf/sr", methods=["POST"])
def pdf_sr():
    from flask import Response
    data = request.form
    try:
        name   = str(data.get("name", "")).strip() or "あなた"
        year   = int(data["year"]); month = int(data["month"]); day = int(data["day"])
        hour   = int(data.get("hour", 12)); minute = int(data.get("minute", 0))
        city   = str(data.get("city", "新潟市")).strip()
        lat    = float(data.get("lat") or 37.9161)
        lng    = float(data.get("lng") or 139.0364)
        sr_year_raw = data.get("sr_year", "")
        sr_year = int(sr_year_raw) if sr_year_raw.strip().isdigit() else None
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400
    try:
        html = generate_solar_return_html(name, year, month, day, hour, minute, city,
                                           lat=lat, lng=lng, tz_str="Asia/Tokyo",
                                           target_year=sr_year)
        pdf  = html_to_pdf_bytes(html)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>PDF生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    from urllib.parse import quote
    yr = sr_year if sr_year else 2026
    fname = f"{name}_{yr}年星読み.pdf"
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"sr.pdf\"; filename*=UTF-8''{quote(fname)}"})


@app.route("/pdf/lifecycle", methods=["POST"])
def pdf_lifecycle():
    from flask import Response
    data = request.form
    try:
        name   = str(data.get("name", "")).strip() or "あなた"
        year   = int(data["year"]); month = int(data["month"]); day = int(data["day"])
        city   = str(data.get("city", "新潟市")).strip()
        lat    = float(data.get("lat") or 37.9161)
        lng    = float(data.get("lng") or 139.0364)
    except (KeyError, ValueError) as e:
        return "<p style='color:red'>入力値が正しくありません。入力内容をご確認ください。</p>", 400
    try:
        html = generate_lifecycle_html(name, year, month, day, city, lat=lat, lng=lng)
        pdf  = html_to_pdf_bytes(html)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>PDF生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    from urllib.parse import quote
    fname = f"{name}_ライフサイクル.pdf"
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"lifecycle.pdf\"; filename*=UTF-8''{quote(fname)}"})


# ── サンプルPDF（GETでダウンロード可能）──
@app.route("/sample/natal/pdf")
def sample_natal_pdf():
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_html_report(s["name"], s["year"], s["month"], s["day"],
                                     s["hour"], s["minute"], s["city"],
                                     lat=s["lat"], lng=s["lng"])
        pdf  = html_to_pdf_bytes(html)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>PDF生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    from urllib.parse import quote
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"sample_natal.pdf\"; filename*=UTF-8''{quote('moonlog_出生チャート_サンプル.pdf')}"})


@app.route("/sample/sr/pdf")
def sample_sr_pdf():
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_solar_return_html(s["name"], s["year"], s["month"], s["day"],
                                           s["hour"], s["minute"], s["city"],
                                           lat=s["lat"], lng=s["lng"],
                                           tz_str="Asia/Tokyo", target_year=2026)
        pdf  = html_to_pdf_bytes(html)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>PDF生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    from urllib.parse import quote
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"sample_sr.pdf\"; filename*=UTF-8''{quote('moonlog_2026年星読み_サンプル.pdf')}"})


@app.route("/sample/lifecycle/pdf")
def sample_lifecycle_pdf():
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_lifecycle_html(s["name"], s["year"], s["month"], s["day"],
                                        s["city"], lat=s["lat"], lng=s["lng"])
        pdf  = html_to_pdf_bytes(html)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>PDF生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    from urllib.parse import quote
    return Response(pdf, mimetype="application/pdf",
                    headers={"Content-Disposition": f"attachment; filename=\"sample_lifecycle.pdf\"; filename*=UTF-8''{quote('moonlog_ライフサイクル_サンプル.pdf')}"})


@app.route("/sample/lifecycle")
def sample_lifecycle():
    from flask import Response
    s = SAMPLE_DATA
    try:
        html = generate_lifecycle_html(s["name"], s["year"], s["month"], s["day"],
                                        s["city"], lat=s["lat"], lng=s["lng"], sample=True)
    except Exception as e:
        import traceback; traceback.print_exc()
        return "<p style='color:red'>サンプル生成中にエラーが発生しました。時間をおいてお試しください。</p>", 500
    return Response(html, mimetype="text/html; charset=utf-8")


# ============================================================
# 個人鑑定レポート
# ============================================================

@app.route("/my_reading")
def my_reading():
    filepath = "/Users/mitsuinatsuki/Documents/星読み/natsuki_chart_reading.html"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<p>読み込みエラー: {e}</p>", 500

@app.route("/hayate_reading")
def hayate_reading():
    filepath = "/Users/mitsuinatsuki/Documents/星読み/hayate_chart_reading.html"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<p>読み込みエラー: {e}</p>", 500

@app.route("/fuuki_reading")
def fuuki_reading():
    filepath = "/Users/mitsuinatsuki/Documents/星読み/fuuki_chart_reading.html"
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            return f.read()
    except Exception as e:
        return f"<p>読み込みエラー: {e}</p>", 500

# ============================================================
# 法的ページ（特商法・プライバシーポリシー・利用規約）
# ============================================================

_LEGAL_CSS = """
<style>
  @import url('https://fonts.googleapis.com/css2?family=Shippori+Mincho:wght@400;500;600&family=Noto+Sans+JP:wght@300;400;500&display=swap');
  :root {
    --base:#FAF6EE; --text-d:#3A3450; --text-m:#6B607A; --text-l:#9B91A8;
    --gold:#B8985A; --gold-d:#8C6E2F; --border:#E8DDD0;
    --serif:'Shippori Mincho',serif; --sans:'Noto Sans JP',sans-serif;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: var(--base); color: var(--text-d); font-family: var(--sans); line-height: 1.9; }
  .legal-header {
    background: white; border-bottom: 1px solid var(--border);
    padding: 1.2rem 2rem; display: flex; align-items: center; gap: 1rem;
  }
  .legal-header a { font-family: var(--serif); font-size: 0.85rem; color: var(--gold-d);
    letter-spacing: 0.18em; text-decoration: none; }
  .legal-header a:hover { text-decoration: underline; }
  .legal-header span { color: var(--text-l); font-size: 0.78rem; }
  .legal-wrap { max-width: 760px; margin: 0 auto; padding: 4rem 2rem 6rem; }
  .legal-wrap h1 {
    font-family: var(--serif); font-size: 1.35rem; font-weight: 500;
    color: var(--text-d); letter-spacing: 0.12em;
    padding-bottom: 1rem; border-bottom: 1px solid var(--border);
    margin-bottom: 2.5rem;
  }
  .legal-wrap h2 {
    font-family: var(--serif); font-size: 0.95rem; font-weight: 600;
    color: var(--gold-d); letter-spacing: 0.1em;
    margin: 2.2rem 0 0.8rem;
  }
  .legal-wrap p, .legal-wrap li {
    font-size: 0.875rem; color: var(--text-m); line-height: 1.95;
    margin-bottom: 0.6rem;
  }
  .legal-wrap ul { padding-left: 1.4rem; }
  .legal-table { width: 100%; border-collapse: collapse; margin: 1rem 0; }
  .legal-table th, .legal-table td {
    border: 1px solid var(--border); padding: 0.7rem 1rem;
    font-size: 0.85rem; text-align: left; vertical-align: top;
  }
  .legal-table th {
    background: #F4EFE6; color: var(--text-d);
    font-weight: 500; width: 30%; white-space: nowrap;
  }
  .legal-table td { color: var(--text-m); }
  .legal-updated { font-size: 0.75rem; color: var(--text-l); margin-top: 3rem; }
  footer.legal-footer {
    text-align: center; padding: 2.5rem; border-top: 1px solid var(--border);
    font-size: 0.72rem; color: var(--text-l); letter-spacing: 0.08em;
  }
</style>
"""

_LEGAL_HEADER = """
<header class="legal-header">
  <a href="/">MOONLOG</a>
  <span>&rsaquo;</span>
  <span>{title}</span>
</header>
"""

_LEGAL_FOOTER = """
<footer class="legal-footer">
  <a href="/blog" style="color:var(--text-l);margin:0 0.8rem;text-decoration:none;">ブログ</a>
  <a href="/glossary" style="color:var(--text-l);margin:0 0.8rem;text-decoration:none;">用語解説</a>
  <a href="/faq" style="color:var(--text-l);margin:0 0.8rem;text-decoration:none;">よくある質問</a>
  <a href="/legal/tokushoho" style="color:var(--text-l);margin:0 0.8rem;text-decoration:none;">特定商取引法</a>
  <a href="/legal/privacy" style="color:var(--text-l);margin:0 0.8rem;text-decoration:none;">プライバシーポリシー</a>
  <a href="/legal/terms" style="color:var(--text-l);margin:0 0.8rem;text-decoration:none;">利用規約</a>
  <p style="margin-top:1rem;">© 2026 MOONLOG. All rights reserved.</p>
</footer>
"""

# ============================================================
# ブログ（SEO集客用）— articles/*.md を Markdown で配信
# DB・管理画面なし。articles/ に .md ファイルを置くだけで記事が増える。
# ============================================================
ARTICLES_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "articles")

# ブログのカテゴリー（key, 表示ラベル）。記事のfrontmatterに category: key を書く。
BLOG_CATEGORIES = [
    ("basic", "基礎・調べ方"),
    ("essay", "自己理解の読みもの"),
    ("yearly", "星座別・年運"),
]
_CAT_LABEL = dict(BLOG_CATEGORIES)

_BLOG_CSS_EXTRA = """
<style>
  .legal-wrap h3 { font-family:var(--serif); font-size:0.9rem; font-weight:600;
    color:var(--text-d); letter-spacing:0.08em; margin:1.8rem 0 0.6rem; }
  .legal-wrap a { color:var(--gold-d); }
  .legal-wrap blockquote {
    border-left:3px solid var(--gold); background:#F4EFE6;
    padding:0.8rem 1.2rem; margin:1.2rem 0; color:var(--text-m); font-size:0.85rem;
  }
  .legal-wrap blockquote p { margin:0; }
  .legal-wrap img { max-width:100%; height:auto; border-radius:4px; margin:1rem 0; }
  .legal-wrap strong { color:var(--text-d); }
  .legal-wrap ol { padding-left:1.4rem; }
  .blog-meta { font-size:0.75rem; color:var(--text-l); margin-bottom:2rem;
    letter-spacing:0.06em; }
  .blog-list-item { display:flex; gap:1.2rem; align-items:flex-start;
    padding:1.4rem 0; border-bottom:1px solid var(--border); }
  .blog-list-thumb { flex-shrink:0; width:128px; height:86px;
    object-fit:cover; border-radius:5px; display:block; }
  .blog-list-body { flex:1; min-width:0; }
  .blog-list-item .d { font-size:0.72rem; color:var(--text-l); margin-bottom:0.3rem; }
  .blog-list-item .blog-list-title { font-family:var(--serif); font-size:1.02rem;
    color:var(--text-d); text-decoration:none; letter-spacing:0.04em; }
  .blog-list-item .blog-list-title:hover { color:var(--gold-d); }
  .blog-list-item .x { font-size:0.82rem; color:var(--text-m); margin-top:0.4rem; }
  .blog-list-item .read-more { display:inline-block; margin-top:0.7rem;
    font-size:0.8rem; color:var(--gold-d); text-decoration:none; letter-spacing:0.06em; }
  .blog-list-item .read-more:hover { text-decoration:underline; }
  .blog-cta { margin-top:3rem; padding:1.8rem; background:white;
    border:1px solid var(--gold); border-radius:6px; text-align:center; }
  .blog-cta p { font-size:0.86rem; color:var(--text-m); margin-bottom:1rem; }
  .blog-cta a { display:inline-block; background:var(--gold-d); color:white;
    text-decoration:none; padding:0.7rem 1.8rem; border-radius:4px;
    font-size:0.85rem; letter-spacing:0.08em; }
  .cat-bar { display:flex; flex-wrap:wrap; gap:0.5rem; margin:0 0 2rem; }
  .cat-chip { font-size:0.76rem; color:var(--text-m); text-decoration:none;
    padding:0.3rem 0.9rem; border:1px solid var(--border); border-radius:999px;
    letter-spacing:0.04em; }
  .cat-chip:hover { border-color:var(--gold); color:var(--gold-d); }
  .cat-chip.cat-on { background:var(--gold-d); color:#fff; border-color:var(--gold-d); }
  .cat-tag { display:inline-block; font-size:0.68rem; color:var(--gold-d);
    background:rgba(184,152,90,0.1); padding:0.15rem 0.6rem; border-radius:3px;
    margin-bottom:0.4rem; letter-spacing:0.04em; }
</style>
"""

def _parse_article(path):
    """Markdownファイルを frontmatter(メタ情報) と本文に分割して返す"""
    with open(path, encoding="utf-8") as f:
        raw = f.read()
    meta = {"title": "", "description": "", "date": "", "thumbnail": "", "category": ""}
    body = raw
    if raw.startswith("---"):
        parts = raw.split("---", 2)
        if len(parts) >= 3:
            fm, body = parts[1], parts[2]
            for line in fm.strip().splitlines():
                if ":" in line:
                    k, v = line.split(":", 1)
                    meta[k.strip()] = v.strip()
    meta["slug"] = os.path.splitext(os.path.basename(path))[0]
    meta["body_md"] = body.strip()
    return meta

def _blog_today():
    """日本時間の今日（YYYY-MM-DD）"""
    import datetime as _dt
    jst = _dt.timezone(_dt.timedelta(hours=9))
    return _dt.datetime.now(jst).date().isoformat()

def _load_articles(show_all=False):
    """全記事を読み込み、日付の新しい順で返す。
    公開日が未来の記事は、その日付になるまで非表示（毎日更新の自動化）。
    show_all=True で未来記事も含める（プレビュー用）。"""
    import glob as _glob
    today = _blog_today()
    arts = []
    if os.path.isdir(ARTICLES_DIR):
        for path in _glob.glob(os.path.join(ARTICLES_DIR, "*.md")):
            try:
                a = _parse_article(path)
                if show_all or a.get("date", "") <= today:
                    arts.append(a)
            except Exception as e:
                print(f"[blog] 記事読み込み失敗 {path}: {e}")
    arts.sort(key=lambda a: a.get("date", ""), reverse=True)
    return arts

@app.route("/blog")
def blog_index():
    cur = request.args.get("cat", "")
    preview = request.args.get("preview") == "1"
    qs = "?preview=1" if preview else ""
    all_arts = _load_articles(show_all=preview)
    present = {a.get("category", "") for a in all_arts}
    arts = [a for a in all_arts if a.get("category", "") == cur] if cur else all_arts
    # カテゴリーフィルタバー（記事が存在するカテゴリーのみ表示）
    cats_html = f'<a class="cat-chip{"" if cur else " cat-on"}" href="/blog{qs}">すべて</a>'
    for key, label in BLOG_CATEGORIES:
        if key in present:
            on = " cat-on" if cur == key else ""
            pv = "&preview=1" if preview else ""
            cats_html += f'<a class="cat-chip{on}" href="/blog?cat={key}{pv}">{_esc(label)}</a>'
    items = ""
    for a in arts:
        slug = _esc(a["slug"])
        thumb = a.get("thumbnail", "")
        thumb_html = (
            f'<a href="/blog/{slug}{qs}"><img class="blog-list-thumb" '
            f'src="{_esc(thumb)}" alt="{_esc(a.get("title",""))}"></a>'
        ) if thumb else ""
        catlabel = _CAT_LABEL.get(a.get("category", ""), "")
        cat_html = f'<span class="cat-tag">{_esc(catlabel)}</span>' if catlabel else ""
        items += (
            f'<div class="blog-list-item">'
            f'{thumb_html}'
            f'<div class="blog-list-body">'
            f'{cat_html}'
            f'<div class="d">{_esc(a.get("date",""))}</div>'
            f'<a class="blog-list-title" href="/blog/{slug}{qs}">{_esc(a.get("title","(無題)"))}</a>'
            f'<div class="x">{_esc(a.get("description",""))}</div>'
            f'<a class="read-more" href="/blog/{slug}{qs}">続きを読む →</a>'
            f'</div>'
            f'</div>'
        )
    if not items:
        items = '<p>このカテゴリーの記事は準備中です。</p>'
    return f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>ブログ｜星と自己理解のはなし | moonlog</title>
<meta name="description" content="星読み・占星術を「自己理解の地図」として使うためのヒントを綴る moonlog のブログです。">
<link rel="canonical" href="https://moonlog.jp/blog">
{_LEGAL_CSS}
{_BLOG_CSS_EXTRA}
</head><body>
{_LEGAL_HEADER.format(title="ブログ")}
<div class="legal-wrap">
  <h1>星と自己理解のはなし</h1>
  <div class="cat-bar">{cats_html}</div>
  {items}
</div>
{_LEGAL_FOOTER}
</body></html>"""

@app.route("/blog/<slug>")
def blog_article(slug):
    from flask import abort
    # slugを英数字・ハイフン・アンダースコアのみに制限（ディレクトリトラバーサル防止）
    safe = "".join(c for c in slug if c.isalnum() or c in "-_")
    path = os.path.join(ARTICLES_DIR, safe + ".md")
    if not safe or not os.path.isfile(path):
        abort(404)
    a = _parse_article(path)
    pv = request.args.get("preview") == "1"
    qs = "?preview=1" if pv else ""
    if not pv and a.get("date", "") > _blog_today():
        abort(404)
    import markdown as _md
    body_html = _md.markdown(a["body_md"], extensions=["extra"])
    title = a.get("title", "") or "記事"
    catkey = a.get("category", "")
    catlabel = _CAT_LABEL.get(catkey, "")
    cat_meta = (f'<a href="/blog?cat={_esc(catkey)}{"&preview=1" if pv else ""}" style="color:var(--gold-d);">{_esc(catlabel)}</a>　｜　') if catlabel else ""
    return f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>{_esc(title)} | moonlog</title>
<meta name="description" content="{_esc(a.get('description',''))}">
<link rel="canonical" href="https://moonlog.jp/blog/{_esc(safe)}">
{_LEGAL_CSS}
{_BLOG_CSS_EXTRA}
</head><body>
{_LEGAL_HEADER.format(title="ブログ")}
<div class="legal-wrap">
  <h1>{_esc(title)}</h1>
  <div class="blog-meta">{cat_meta}{_esc(a.get("date",""))}　｜　<a href="/blog{qs}" style="color:var(--text-l);">ブログ一覧</a></div>
  {body_html}
  <div class="blog-cta">
    <p>moonlogでは、あなたの星の配置から「自分という地図」を読み解くレポートを無料でお試しいただけます。</p>
    <a href="/#form-section">出生チャート 無料体験版をためす</a>
  </div>
</div>
{_LEGAL_FOOTER}
</body></html>"""

@app.route("/sitemap.xml")
def sitemap_xml():
    from flask import Response
    base = "https://moonlog.jp"
    urls = ["/", "/blog", "/glossary", "/faq",
            "/legal/tokushoho", "/legal/privacy", "/legal/terms"]
    for a in _load_articles():
        urls.append(f"/blog/{a['slug']}")
    body = '<?xml version="1.0" encoding="UTF-8"?>\n'
    body += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u in urls:
        body += f"  <url><loc>{base}{u}</loc></url>\n"
    body += '</urlset>\n'
    return Response(body, mimetype="application/xml")

@app.route("/legal/tokushoho")
def legal_tokushoho():
    html = f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>特定商取引法に基づく表記 | MOONLOG</title>
{_LEGAL_CSS}
</head><body>
{_LEGAL_HEADER.format(title="特定商取引法に基づく表記")}
<div class="legal-wrap">
  <h1>特定商取引法に基づく表記</h1>
  <table class="legal-table">
    <tr><th>販売事業者</th><td>三井夏紀</td></tr>
    <tr><th>所在地</th><td>東京都（詳細住所は請求があった場合に遅滞なく開示いたします）</td></tr>
    <tr><th>電話番号</th><td>請求があった場合に遅滞なく開示いたします</td></tr>
    <tr><th>メールアドレス</th><td>{CONTACT_EMAIL}</td></tr>
    <tr><th>販売URL</th><td>https://moonlog.jp</td></tr>
    <tr><th>販売価格</th><td>各レポートページに表示の価格（税込）<br>出生チャート（ホロスコープ鑑定）レポート ¥980 / 2026年 星読みレポート ¥980 / 仕事・お金・恋愛 3分野レポート ¥980<br><small style="color:#9A8870;">※ 有料レポートは{RELEASE_DATE_JP}リリース予定</small></td></tr>
    <tr><th>販売価格以外の費用</th><td>なし（インターネット接続料・通信料はお客様のご負担となります）</td></tr>
    <tr><th>支払方法</th><td>クレジットカード（Visa / Mastercard / American Express / JCB）</td></tr>
    <tr><th>支払時期</th><td>購入手続き完了時にお支払いが確定します</td></tr>
    <tr><th>商品の引き渡し時期</th><td>決済完了後、即時にレポートを画面表示およびご登録メールアドレスにPDFをお届けします</td></tr>
    <tr><th>返品・キャンセル</th><td>デジタルコンテンツの性質上、購入完了後の返金・キャンセルはお受けできません。ご不明な点はご購入前にお問い合わせください</td></tr>
    <tr><th>動作環境</th><td>最新版の主要ブラウザ（Chrome / Safari / Firefox / Edge）推奨</td></tr>
  </table>
  <p class="legal-updated">最終更新日：2026年5月13日</p>
</div>
{_LEGAL_FOOTER}
</body></html>"""
    return html

@app.route("/legal/privacy")
def legal_privacy():
    html = f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>プライバシーポリシー | MOONLOG</title>
{_LEGAL_CSS}
</head><body>
{_LEGAL_HEADER.format(title="プライバシーポリシー")}
<div class="legal-wrap">
  <h1>プライバシーポリシー</h1>
  <p>MOONLOG（以下「当サービス」）は、ご利用者の個人情報の保護を重要事項と考え、以下のとおりプライバシーポリシーを定めます。</p>

  <h2>1. 収集する情報</h2>
  <p>当サービスでは、レポート生成のために以下の情報を取得します。</p>
  <ul>
    <li>お名前（ニックネーム可）</li>
    <li>生年月日・出生時刻・出生地</li>
    <li>メールアドレス（有料レポートのお届けに使用）</li>
    <li>決済情報（Stripe社のシステムを経由して処理し、当サービスはカード番号を保持しません）</li>
  </ul>

  <h2>2. 利用目的</h2>
  <ul>
    <li>ホロスコープ・レポートの生成および提供</li>
    <li>購入レポートのメール送信</li>
    <li>サービス改善・統計分析（個人を特定しない形式）</li>
    <li>お問い合わせへの回答</li>
  </ul>

  <h2>3. 第三者への提供</h2>
  <p>当サービスは、以下の場合を除き、取得した個人情報を第三者に提供しません。</p>
  <ul>
    <li>法令に基づく場合</li>
    <li>決済処理のためStripe, Inc.へ必要情報を提供する場合</li>
  </ul>

  <h2>4. 安全管理</h2>
  <p>個人情報への不正アクセス・紛失・破損・改ざんを防ぐため、適切なセキュリティ対策を講じます。</p>

  <h2>5. Cookieの利用</h2>
  <p>当サービスはセッション管理のためCookieを使用することがあります。ブラウザの設定によりCookieを無効化できますが、一部機能が制限される場合があります。</p>

  <h2>6. 情報の開示・訂正・削除</h2>
  <p>ご自身の個人情報の開示・訂正・削除をご希望の場合は、下記連絡先までお問い合わせください。</p>

  <h2>7. お問い合わせ</h2>
  <p>{CONTACT_EMAIL}</p>

  <p class="legal-updated">最終更新日：2026年4月30日</p>
</div>
{_LEGAL_FOOTER}
</body></html>"""
    return html

@app.route("/legal/terms")
def legal_terms():
    html = f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>利用規約 | MOONLOG</title>
{_LEGAL_CSS}
</head><body>
{_LEGAL_HEADER.format(title="利用規約")}
<div class="legal-wrap">
  <h1>利用規約</h1>
  <p>本利用規約（以下「本規約」）は、MOONLOG（以下「当サービス」）の利用条件を定めるものです。ご利用の前に必ずお読みください。</p>

  <h2>第1条（適用）</h2>
  <p>本規約は、当サービスを利用するすべてのお客様に適用されます。サービスを利用した時点で本規約に同意したものとみなします。</p>

  <h2>第2条（サービスの内容）</h2>
  <p>当サービスは、出生情報をもとにホロスコープデータを計算し、占星術の解釈テキストを自動生成・提供するデジタルコンテンツサービスです。占星術師による個別の対面・対話鑑定は含まれません。</p>

  <h2>第3条（免責事項）</h2>
  <ul>
    <li>本レポートは占星術データに基づく参考情報であり、将来を確約・保証するものではありません</li>
    <li>医療・法律・投資等の専門的判断の代替としてご利用いただくことはできません</li>
    <li>出生時刻・場所の誤入力による結果の相違について、当サービスは責任を負いません</li>
    <li>天災・通信障害等の不可抗力によるサービス停止・データ消失について免責とします</li>
  </ul>

  <h2>第4条（禁止事項）</h2>
  <ul>
    <li>生成されたレポートの無断転載・複製・販売</li>
    <li>当サービスへの不正アクセス・過度な負荷をかける行為</li>
    <li>他者を誹謗中傷する目的での利用</li>
    <li>法令または公序良俗に反する行為</li>
  </ul>

  <h2>第5条（知的財産権）</h2>
  <p>当サービスのデザイン・テキスト・ロゴ等の知的財産権は当サービス運営者に帰属します。生成されたレポートは購入者個人の利用に限り使用できます。</p>

  <h2>第6条（料金・返金）</h2>
  <p>有料レポートの価格は各ページに表示の金額（税込）とします。デジタルコンテンツの性質上、購入後の返金・キャンセルはお受けできません。</p>

  <h2>第7条（規約の変更）</h2>
  <p>当サービスは必要に応じて本規約を変更できるものとします。変更後のご利用をもって変更内容に同意したとみなします。</p>

  <h2>第8条（準拠法・管轄）</h2>
  <p>本規約は日本法に準拠し、東京地方裁判所を第一審の専属的合意管轄裁判所とします。</p>

  <p class="legal-updated">最終更新日：2026年4月30日</p>
</div>
{_LEGAL_FOOTER}
</body></html>"""
    return html


# ============================================================
# 用語解説 / よくある質問
# ============================================================

_GLOSSARY_CSS_EXTRA = """
<style>
  .glossary-toc {
    background: #FFFFFF; border: 1px solid var(--border); border-radius: 6px;
    padding: 1.4rem 1.8rem; margin-bottom: 2.5rem;
  }
  .glossary-toc-title {
    font-family: var(--serif); font-size: 0.78rem;
    color: var(--gold-d); letter-spacing: 0.18em;
    margin-bottom: 0.8rem; font-weight: 600;
  }
  .glossary-toc ul { list-style: none; padding: 0; margin: 0;
                     display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
                     gap: 0.4rem 1.4rem; }
  .glossary-toc li { font-size: 0.82rem; margin: 0; }
  .glossary-toc a { color: var(--text-d); text-decoration: none;
                    border-bottom: 1px dashed transparent; transition: border-color .2s; }
  .glossary-toc a:hover { border-bottom-color: var(--gold); color: var(--gold-d); }
  .term {
    background: #FFFFFF; border: 1px solid var(--border); border-radius: 6px;
    padding: 1.6rem 2rem; margin-bottom: 1.4rem;
  }
  .term h2 {
    font-family: var(--serif); font-size: 1.05rem; font-weight: 600;
    color: var(--text-d) !important; margin: 0 0 0.4rem !important;
    letter-spacing: 0.06em;
  }
  .term-en {
    font-family: 'Cormorant Garamond', serif; font-style: italic;
    font-size: 0.78rem; color: var(--gold-d); letter-spacing: 0.12em;
    margin-bottom: 1rem;
  }
  .term p { font-size: 0.86rem !important; line-height: 2 !important; color: var(--text-m); }
  .term .key { color: var(--text-d); font-weight: 600; background: #F8F0E0; padding: 1px 6px; border-radius: 3px; }
  .term-table { width: 100%; border-collapse: collapse; margin: 0.8rem 0; }
  .term-table th, .term-table td {
    border: 1px solid var(--border); padding: 0.55rem 0.9rem;
    font-size: 0.82rem; text-align: left; vertical-align: top;
  }
  .term-table th { background: #F4EFE6; color: var(--text-d); font-weight: 500; }
  .faq-item {
    background: #FFFFFF; border: 1px solid var(--border); border-radius: 6px;
    padding: 1.4rem 1.8rem; margin-bottom: 1rem;
  }
  .faq-q {
    font-family: var(--serif); font-weight: 600; color: var(--text-d);
    font-size: 0.95rem; letter-spacing: 0.04em; margin-bottom: 0.7rem;
    display: flex; gap: 0.6rem; align-items: flex-start;
  }
  .faq-q::before { content: "Q."; color: var(--gold-d); font-family: 'Cormorant Garamond',serif;
                    font-style: italic; font-weight: 600; font-size: 1rem; flex-shrink: 0; }
  .faq-a { font-size: 0.85rem; color: var(--text-m); line-height: 2;
           padding-left: 1.6rem; }
  .faq-a a { color: var(--gold-d); }
</style>
"""

@app.route("/glossary")
def glossary_page():
    html = f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>用語解説 | MOONLOG</title>
{_LEGAL_CSS}
{_GLOSSARY_CSS_EXTRA}
</head><body>
{_LEGAL_HEADER.format(title="用語解説")}
<div class="legal-wrap">
  <h1>用語解説</h1>
  <p style="margin-bottom:2rem;">レポートを読むときに知っておくと役立つ占星術の基本用語をまとめました。</p>

  <div class="glossary-toc">
    <div class="glossary-toc-title">📋 目次</div>
    <ul>
      <li><a href="#chart">出生チャート（ネイタル）</a></li>
      <li><a href="#sign">サイン（12星座）</a></li>
      <li><a href="#house">ハウス（12室）</a></li>
      <li><a href="#planet">惑星（7惑星）</a></li>
      <li><a href="#aspect">アスペクト</a></li>
      <li><a href="#solar-return">ソーラーリターン</a></li>
      <li><a href="#transit">トランジット</a></li>
    </ul>
  </div>

  <div class="term" id="chart">
    <h2>出生チャート（ネイタルチャート）</h2>
    <div class="term-en">Birth Chart / Natal Chart</div>
    <p>あなたが生まれた瞬間の、太陽・月・惑星の配置図です。一生変わらない「あなたの設計図」のようなもの。<span class="key">生年月日・出生時刻・出生地</span>の3つから計算します。性格・才能・人生のテーマなど、生まれ持った傾向を読み解く基礎になります。</p>
  </div>

  <div class="term" id="sign">
    <h2>サイン（12星座）</h2>
    <div class="term-en">Sign / Zodiac</div>
    <p>天空を黄道上で12等分した区画のこと。牡羊座から魚座まで12個あり、それぞれに性質・キャラクターがあります。</p>
    <p>サインは <span class="key">「どんなふうに」</span> を示します。たとえば牡羊座は直球・スピード重視、おうし座はゆっくり・確実、ふたご座は多角的・柔軟、というように。</p>
    <table class="term-table">
      <tr><th>記号</th><th>サイン</th><th>キーワード</th></tr>
      <tr><td>♈</td><td>牡羊座</td><td>始動・直球・チャレンジ</td></tr>
      <tr><td>♉</td><td>牡牛座</td><td>安定・五感・蓄積</td></tr>
      <tr><td>♊</td><td>双子座</td><td>知性・対話・柔軟</td></tr>
      <tr><td>♋</td><td>蟹座</td><td>感情・家族・養育</td></tr>
      <tr><td>♌</td><td>獅子座</td><td>表現・誇り・創造</td></tr>
      <tr><td>♍</td><td>乙女座</td><td>分析・実務・改善</td></tr>
      <tr><td>♎</td><td>天秤座</td><td>調和・関係性・美</td></tr>
      <tr><td>♏</td><td>蠍座</td><td>深化・変容・本質</td></tr>
      <tr><td>♐</td><td>射手座</td><td>探究・自由・哲学</td></tr>
      <tr><td>♑</td><td>山羊座</td><td>達成・責任・戦略</td></tr>
      <tr><td>♒</td><td>水瓶座</td><td>革新・自由・コミュニティ</td></tr>
      <tr><td>♓</td><td>魚座</td><td>感受性・癒し・直感</td></tr>
    </table>
  </div>

  <div class="term" id="house">
    <h2>ハウス（12室）</h2>
    <div class="term-en">House</div>
    <p>地球から見た天空を、地平線と子午線を基準に12分割した区画です。1ハウスから12ハウスまであり、それぞれに「人生の分野」が割り当てられています。</p>
    <p>ハウスは <span class="key">「どこで」</span> を示します。サインが「どんなふうに」なのに対し、ハウスは「人生のどの場面で」を表します。</p>
    <p>※ ハウスは出生時刻と出生地が必要です。時刻が分からないと正確には読めません。</p>
    <p>※ moonlog では <strong>Koch（コッホ）</strong>方式でハウスを計算しています。</p>
    <table class="term-table">
      <tr><th>ハウス</th><th>分野</th></tr>
      <tr><td>1ハウス</td><td>あなた自身の在り方・第一印象</td></tr>
      <tr><td>2ハウス</td><td>お金・豊かさ・価値観</td></tr>
      <tr><td>3ハウス</td><td>学び・コミュニケーション</td></tr>
      <tr><td>4ハウス</td><td>家族・家庭・プライベート</td></tr>
      <tr><td>5ハウス</td><td>創造・喜び・恋愛</td></tr>
      <tr><td>6ハウス</td><td>日々の仕事と健康</td></tr>
      <tr><td>7ハウス</td><td>パートナーシップ</td></tr>
      <tr><td>8ハウス</td><td>変容・深化・再生</td></tr>
      <tr><td>9ハウス</td><td>旅・学び・大きなビジョン</td></tr>
      <tr><td>10ハウス</td><td>キャリア・社会での立ち位置</td></tr>
      <tr><td>11ハウス</td><td>仲間・コミュニティ・夢</td></tr>
      <tr><td>12ハウス</td><td>内側の世界・精神性・癒し</td></tr>
    </table>
  </div>

  <div class="term" id="planet">
    <h2>惑星（7惑星）</h2>
    <div class="term-en">Planets</div>
    <p>占星術では、太陽・月・水星・金星・火星・木星・土星の7つを基本の天体として扱います。それぞれが人生の異なる側面を象徴しています。</p>
    <table class="term-table">
      <tr><th>記号</th><th>惑星</th><th>表すもの</th></tr>
      <tr><td>☉</td><td>太陽</td><td>社会的な顔・人生のテーマ</td></tr>
      <tr><td>☽</td><td>月</td><td>感情・内面・心の安らぎ</td></tr>
      <tr><td>☿</td><td>水星</td><td>思考・言葉・コミュニケーション</td></tr>
      <tr><td>♀</td><td>金星</td><td>愛・喜び・美意識</td></tr>
      <tr><td>♂</td><td>火星</td><td>行動力・情熱・エネルギー</td></tr>
      <tr><td>♃</td><td>木星</td><td>発展・幸運・拡大</td></tr>
      <tr><td>♄</td><td>土星</td><td>課題・成熟・魂のテーマ</td></tr>
    </table>
  </div>

  <div class="term" id="aspect">
    <h2>アスペクト</h2>
    <div class="term-en">Aspect</div>
    <p>惑星と惑星が作る「角度」のこと。0度・60度・90度・120度・180度などの特定の角度のとき、その2つの惑星のエネルギーが響き合います。</p>
    <p>たとえば「太陽と月が90度（スクエア）」だと、社会的な自分と感情的な自分の間に緊張がある——というふうに読みます。アスペクトは個性の深い部分を映し出します。</p>
  </div>

  <div class="term" id="solar-return">
    <h2>ソーラーリターン（SR）</h2>
    <div class="term-en">Solar Return</div>
    <p>出生時の太陽と全く同じ位置に、運行中（トランジット）の太陽が戻ってくる瞬間のこと。だいたい誕生日の前後2日以内に起きます。</p>
    <p>その瞬間を中心に新しいチャートを作って読むのが <span class="key">「2026年 星読み」</span> レポートです。1年に1度しか起きない宇宙的なイベントが、その年の「種」になるという考え方。</p>
    <p>SRチャートは1年ごとに違う配置になります。前年と今年で何が変わったかを比べることで、その年に起きるテーマが立体的に見えてきます。</p>
  </div>

  <div class="term" id="transit">
    <h2>トランジット</h2>
    <div class="term-en">Transit</div>
    <p>「現在運行中の」という意味。リアルタイムで動いている惑星の配置を指します。</p>
    <p>「トランジットの木星があなたの月とコンジャンクション（重なる）」のように、出生チャートの星と現在の星の関係を読むことで、いま何が起きているか・これから何が来るかを読み取れます。</p>
  </div>

  <p class="legal-updated">最終更新日：2026年5月13日</p>
</div>
{_LEGAL_FOOTER}
</body></html>"""
    return html


@app.route("/faq")
def faq_page():
    html = f"""<!DOCTYPE html><html lang="ja"><head>
<script async src="https://www.googletagmanager.com/gtag/js?id=G-KT19PT0DDG"></script>
<script>window.dataLayer=window.dataLayer||[];function gtag(){{dataLayer.push(arguments);}}gtag('js',new Date());gtag('config','G-KT19PT0DDG');</script>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1.0">
<title>よくある質問 | MOONLOG</title>
{_LEGAL_CSS}
{_GLOSSARY_CSS_EXTRA}
</head><body>
{_LEGAL_HEADER.format(title="よくある質問")}
<div class="legal-wrap">
  <h1>よくある質問</h1>
  <p style="margin-bottom:1.5rem;">ご利用前によくいただくご質問をまとめました。
    用語については <a href="/glossary" style="color:var(--gold-d);">用語解説ページ</a> もあわせてご覧ください。</p>

  <div style="background:rgba(184,152,88,.08);border:1px dashed var(--gold);border-radius:4px;padding:1rem 1.4rem;margin-bottom:2.5rem;line-height:1.85;">
    <strong style="color:var(--gold-d);">🌙 現在ソフトローンチ期間中</strong><br>
    <span style="font-size:.92rem;">現在は <strong>出生チャート 無料体験版</strong> のみご利用いただけます。<br>
    有料レポート（出生チャート・2026年星読み・3分野レポート）は <strong>{RELEASE_DATE_JP}</strong> リリース予定です。</span>
  </div>

  <h2>月タイプ診断について</h2>

  <div class="faq-item">
    <div class="faq-q">月タイプ診断ってなんですか？太陽星座（ふつうの星座）とは違うんですか？</div>
    <div class="faq-a">
      月タイプ診断は、生まれた瞬間の <strong>「月」の位置</strong> から、あなたの素のあなた（内面・感情）を <strong>12タイプの動物</strong> で読み解く無料の診断です。<br><br>
      雑誌などでよく知られている「いて座」「かに座」などは <strong>太陽星座</strong>——社会的な役割や「人から見える顔」を表します。一方、<strong>月星座</strong> は <strong>心の奥・素の自分</strong> を表す、もう一つの星座です。<br><br>
      たとえば「太陽は蟹座、月は射手座」の人なら、表向きは家庭的に見えても、心の中では自由と冒険を求めている——という具合に、太陽と月で別の顔を持っていることが多いんです。月星座のほうが、自分でも気づきにくい本音を映してくれます。<br><br>
      月タイプ診断では、その月星座を <strong>動物のタイプ</strong> に置き換えて、素のあなたに名前をつけます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">自分の月星座を知らないのですが、大丈夫？</div>
    <div class="faq-a">
      大丈夫です。生年月日と出生時刻・出生地を入力すれば、こちらで <strong>月星座を自動で計算します</strong>。結果ページで「あなたの月は○○座」と表示されます。<br>
      ※ 月星座は太陽星座と違って約2.5日で変わるため、特に出生時刻が分かるとより正確に判定できます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">月タイプ診断と「出生チャート」はどう違うんですか？</div>
    <div class="faq-a">
      <strong>月タイプ診断（無料）</strong> は「月」だけにフォーカスして、動物のタイプとひとことで「素のあなた」を伝えるもの。気軽に・すぐ・シェアできる入口です。<br><br>
      <strong>出生チャート（有料・¥980）</strong> は、月を含めた <strong>7天体＋アセンダント</strong>（太陽・月・水星・金星・火星・木星・土星・ASC）を文章でじっくり読み解く、あなたという地図の全体像です。<br><br>
      同じ「月」も、診断では動物のタイプとして、出生チャートでは7つの星のひとつとして——別の角度から味わえます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">無料診断と有料レポートで、月星座（月のサイン）が違っていることがあります。どちらが正しいのですか？</div>
    <div class="faq-a">
      生まれた瞬間に <strong>月がサインの境目付近にいた方</strong> に、ごくまれに起こります。月は約2.5日で次のサインへ移動するため、出生時刻や出生地によって判定が変わることがあるのです。<br><br>
      ・<strong>月タイプ診断・出生チャート 無料体験版</strong>：出生地を入れなくても気軽に試せるよう、東京を基準に計算しています。<br>
      ・<strong>出生チャート（有料）</strong>：ご入力いただいた出生時刻・出生地で厳密に計算します。<br><br>
      したがって、月がサインの境目近くにいた方は、有料レポートのほうが <strong>正確</strong> です。境目から離れている方（多くの方）はどちらも同じ結果になります。
    </div>
  </div>

  <h2>レポートについて</h2>

  <div class="faq-item">
    <div class="faq-q">出生時刻が正確にわからないのですが、レポートは作れますか？</div>
    <div class="faq-a">
      作成可能ですが、精度に違いがあります。<br>
      ・<strong>出生チャート 無料体験版</strong>：生年月日のみで作成可能です（太陽・月のサインを読みます）。<br>
      ・<strong>有料レポート（{RELEASE_DATE_MD}リリース予定）</strong>：出生時刻が必要です。不明な場合は12:00で計算しますが、ハウスや天頂（MC）の精度は下がります。<br>
      母子手帳・親に確認・病院への問い合わせなどで分かることが多いので、可能なら確認をおすすめします。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">星読みは「占い」ですか？当たるんですか？</div>
    <div class="faq-a">
      moonlogは「占い」ではなく <strong>「自己理解のためのフレームワーク」</strong> として星読みを使っています。「当たる・当たらない」ではなく、<strong>「こういう傾向を持って生まれた人は、こういう環境で力を発揮しやすい」</strong> という読み方です。<br>
      占い師による個別鑑定ではなく、出生時刻の天体配置を計算してデータベースから自動生成するレポートです。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">レポートはいつ届きますか？</div>
    <div class="faq-a">
      決済完了後、すぐに画面でレポートをご覧いただけます。同時にご登録メールアドレスにPDFをお届けします（数分以内）。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">有料レポートは、PDFとブラウザどちらで読めますか？</div>
    <div class="faq-a">
      両方ですが、役割が違います。<br>
      ・<strong>ブラウザ表示</strong>：購入直後にその場ですぐ読めます。ただし<strong>タブを閉じると再アクセスはできません</strong>（ページのURLを再度開いても表示されません）。<br>
      ・<strong>PDF</strong>：購入直後にメールで届く、お手元に残る永久保存版です。<strong>いつでも・何度でも・どの端末でも</strong>読み返せます。<br>
      → 後で読み返したいときは、必ず<strong>メールで届いたPDFをご利用ください</strong>。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">ブラウザのタブを閉じてしまったら、もう読めない？</div>
    <div class="faq-a">
      <strong>有料レポート</strong>の場合：ブラウザでは再表示できませんが、メールで届いたPDFがお手元に残っていますので、そちらをお開きください。PDFは永久保存版なので、いつでも何度でも読み返せます。<br>
      <strong>出生チャート 無料体験版</strong>の場合：PDFのお届けはありませんが、トップページで生年月日を入力すれば、いつでも何度でも表示できます。<br>
      ※ もしPDFが届いていない場合は、迷惑メールフォルダをご確認のうえ、それでも見当たらないときはお問い合わせください。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">スマートフォンでも読めますか？</div>
    <div class="faq-a">
      はい、PC・スマホ・タブレットすべてに対応しています。PDFはどの端末でもレイアウトを保ったままご覧いただけます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">一度買ったレポートは何度も読み返せますか？</div>
    <div class="faq-a">
      はい。お届けしたPDFはお手元にずっと残るので、いつでも何度でも読み返せます。クラウドに保存しておけば、機種変更後も引き続きご利用いただけます。
    </div>
  </div>

  <h2>商品の違いについて</h2>

  <div class="faq-item">
    <div class="faq-q">レポートの種類はどう違うのですか？</div>
    <div class="faq-a">
      <strong>切り口</strong>で違います。<br>
      ・<strong>出生チャート 無料体験版</strong>：太陽・月のさわり（今すぐ読める）<br>
      ・<strong>出生チャート</strong>（{RELEASE_DATE_MD}〜）：あなたが何者か——7惑星すべての完全版<br>
      ・<strong>2026年 星読み</strong>（{RELEASE_DATE_MD}〜）：今年のテーマと流れ<br>
      ・<strong>仕事・お金・恋愛 3分野レポート</strong>（{RELEASE_DATE_MD}〜）：関心の高い3分野を一冊で<br>
      まずは出生チャート 無料体験版から試して、リリース後に興味のあるレポートへどうぞ。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">出生チャート 無料体験版と有料の出生チャートはどう違いますか？</div>
    <div class="faq-a">
      <strong>出生チャート 無料体験版</strong>は太陽・月の2天体のみ。あなたの核となる部分のさわりが読めます。<br>
      <strong>有料の出生チャート（¥980・{RELEASE_DATE_MD}リリース予定）</strong>は7惑星すべて＋総合まとめ＋ホロスコープチャートの完全版。A4換算 約20ページのボリュームです。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">2026年星読みは毎年買い直すのですか？</div>
    <div class="faq-a">
      はい。星の配置は毎年変わるため、年ごとに新しいレポートになります。来年（2027年）になったら2027年版が買えるようになります。
    </div>
  </div>

  <h2>料金・支払いについて</h2>

  <div class="faq-item">
    <div class="faq-q">どうしてこんなに安いの？（¥980）</div>
    <div class="faq-a">
      <strong>必要なときに気軽に使ってほしい</strong>からです。占星術の鑑定は数千〜数万円のものが多く、月額課金サービスもありますが、moonlogは「迷ったときに開ける、手頃な地図」を目指しています。<br>
      ※ オープン記念価格です。順次改定予定です。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">月額課金やサブスクはありますか？</div>
    <div class="faq-a">
      ありません。すべて1回購入の買い切り型です。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">支払い方法は何がありますか？</div>
    <div class="faq-a">
      クレジットカード決済のみご利用いただけます（Visa / Mastercard / American Express / JCB）。<br>
      購入手続きの完了時にお支払いが確定します。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">クレジットカード情報はmoonlogに保存されますか？</div>
    <div class="faq-a">
      <strong>いいえ。moonlogがカード番号を受け取ったり保存したりすることは一切ありません。</strong><br>
      カード決済は、世界中で広く使われている決済サービス <strong>Stripe</strong> を通じて行われます。カード番号の入力と処理はすべてStripeの安全な画面上で完結し、moonlog側にはカード情報が渡りません。安心してご利用ください。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">返金はできますか？</div>
    <div class="faq-a">
      レポートの性質上、購入後の返金は原則お受けしていません。詳しくは <a href="/legal/tokushoho">特定商取引法に基づく表記</a> をご確認ください。<br>
      不明点があれば購入前にお問い合わせください。
    </div>
  </div>

  <h2>個人情報・プライバシーについて</h2>

  <div class="faq-item">
    <div class="faq-q">入力した個人情報はどう扱われますか？</div>
    <div class="faq-a">
      レポート生成のためだけに使用し、第三者には提供しません。詳しくは <a href="/legal/privacy">プライバシーポリシー</a> をご覧ください。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">アカウント登録は必要ですか？</div>
    <div class="faq-a">
      <strong>出生チャート 無料体験版</strong>はアカウント登録不要、すぐにご利用いただけます。<br>
      <strong>有料レポート</strong>はメールアドレスのご登録が必要です（PDFのお届け先）。
    </div>
  </div>

  <h2>レポートの作り方・解釈について</h2>

  <div class="faq-item">
    <div class="faq-q">レポートはどうやって作られていますか？</div>
    <div class="faq-a">
      生年月日・出生時刻・出生地から <strong>swisseph（スイス天文暦）</strong> という標準的な天文計算ライブラリを使って、生まれた瞬間の天体配置を正確に算出しています。
      その配置（惑星のサイン・ハウス）を、moonlog独自の解説データベースと突き合わせて、自動で文章を組み立てています。<br>
      <strong>占い師による個別鑑定ではなく、データに基づく自動生成</strong>のレポートです。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">プロの占星術師の鑑定とは何が違いますか？</div>
    <div class="faq-a">
      moonlogは <strong>「自己理解の入口」</strong> として設計されています。プロ鑑定との主な違い：<br>
      ・<strong>アスペクト（惑星間の角度）の解釈</strong>：moonlogではコンジャンクション（重なり）など主要なものに限定。複雑な角度の組み合わせは扱いません<br>
      ・<strong>ディグニティ（惑星の品位）</strong>：簡略化しています<br>
      ・<strong>逆行</strong>：チャート図に表示しますが、解釈には深く反映していません<br>
      より深い分析や個別の悩み相談には、信頼できる占星術師への対面鑑定をおすすめします。<br>
      moonlogは「自分という地図を確かめるツール」であり、人生の指針を一方的に決めるものではありません。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">解釈の流派・ハウスシステムは何を使っていますか？</div>
    <div class="faq-a">
      現代占星術（西洋占星術の心理学的アプローチ）をベースにしています。<br>
      ハウスシステムは <strong>Koch（コッホ）</strong> を採用。出生時刻に基づいて精度の高いハウス分割ができる方式です。<br>
      なお、よく使われる Placidus（プラシダス）と Koch では、1・4・7・10ハウスのカスプ（ASC・IC・DSC・MC）は同じで、その他のハウスのカスプ位置がわずかに異なります。<br>
      各惑星×サイン・ハウスの解釈は、現代占星術の標準的なテキストを参考にしながら、moonlogのコンセプト（自己受容・後悔のない後半生）に合わせて言葉を選んでいます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">レポートの「☀ 太陽　家族・家庭・プライベート」みたいな表記は、太陽星座のことですか？</div>
    <div class="faq-a">
      いいえ、それは <strong>太陽が今いる「人生の分野（ハウス）」</strong> を示しています。<br>
      たとえば「☀ 太陽　家族・家庭・プライベート」は、<strong>太陽が4ハウス（家族・家庭の分野）に位置している</strong> という意味で、太陽星座が蟹座という意味ではありません。<br>
      ・<strong>サイン（12星座）</strong>＝ どんなふうに（性質・キャラクター）<br>
      ・<strong>ハウス（12室）</strong>＝ どこで（人生のどの分野）<br>
      詳しくは <a href="/glossary#sign" style="color:var(--gold-d);">用語解説</a> をご覧ください。<br>
      なお、レポートでは <strong>太陽・月・火星・木星・土星はハウス</strong>（人生の分野）で、<strong>水星・金星はサイン</strong>（星座）で表示しています。これは出生時刻による精度の違いによるものです。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">解釈に違和感を感じたときはどう読めばいいですか？</div>
    <div class="faq-a">
      レポートの解釈は<strong>「あなたの傾向の一面」</strong>です。一字一句が当てはまるとは限りません。「これは自分っぽい」と感じる部分は受け取って、ピンとこない部分は <strong>「今の自分には響かない」と置いておいて</strong> 構いません。<br>
      占星術は、星から人生を決めつけるものではなく、<strong>自分を見つめ直すきっかけを与える</strong>道具です。違和感のある記述があれば、なぜそう感じたかを考えること自体が、自己理解を深めるヒントになります。
    </div>
  </div>

  <h2>その他</h2>

  <div class="faq-item">
    <div class="faq-q">占星術の知識がなくても読めますか？</div>
    <div class="faq-a">
      はい。専門用語は最小限に、わかりやすい言葉で書いています。記号や用語の意味は <a href="/glossary">用語解説ページ</a> でいつでも確認できます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">家族や友人にプレゼントできますか？</div>
    <div class="faq-a">
      はい。受け取る方の生年月日があれば、その方のレポートを生成できます。お届けPDFをそのままプレゼントできます。
    </div>
  </div>

  <div class="faq-item">
    <div class="faq-q">サンプルを見たいです。</div>
    <div class="faq-a">
      各レポートのサンプルをご用意しています。<br>
      ・<a href="/sample/natal">出生チャート サンプル</a><br>
      ・<a href="/sample/sr">2026年 星読み サンプル</a><br>
      ・<a href="/sample/field_report">仕事・お金・恋愛 3分野レポート サンプル</a>
    </div>
  </div>

  <p class="legal-updated">最終更新日：2026年5月13日</p>
</div>
{_LEGAL_FOOTER}
</body></html>"""
    return html


# ============================================================
# 起動
# ============================================================

if __name__ == "__main__":
    print("\n" + "="*50)
    print("  ✨ 星読みレポート Web アプリ起動 ✨")
    print("="*50)
    print("\n  ブラウザで以下のURLを開いてください:")
    print("  👉  http://localhost:8080")
    print("\n  ファイルを保存するとサーバーが自動再起動します。")
    print("  ブラウザで Cmd+R を押すだけで最新版が表示されます。\n")
    app.run(debug=True, port=8080, host="127.0.0.1", use_reloader=True)

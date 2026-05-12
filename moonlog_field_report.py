# -*- coding: utf-8 -*-
"""
3分野レポート（仕事・お金・恋愛）HTML生成モジュール
moonlog本体に統合するための実装
"""
import os, sys, html as htmllib

# drafts 配下からテキストデータベースをimport
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "drafts"))

from field_report_work_draft import (
    WORK_SUN_CORE, WORK_MARS_STYLE, WORK_MC_VOCATION,
    WORK_SUN_CAUTION, WORK_SUN_PUSH
)
from field_report_money_draft import (
    MONEY_VENUS_CORE, MONEY_SPEND_STYLE, MONEY_JUPITER_WEALTH,
    MONEY_VENUS_CAUTION, MONEY_VENUS_PUSH
)
from field_report_love_draft import (
    LOVE_VENUS_CORE, LOVE_MARS_ATTRACTION, LOVE_MOON_NEEDS,
    LOVE_VENUS_CAUTION, LOVE_VENUS_PUSH
)
from field_report_age_notes import (
    WORK_AGE_NOTE, MONEY_AGE_NOTE, LOVE_AGE_NOTE, age_to_phase
)

# kerykeion で計算
from kerykeion import AstrologicalSubject

SIGNS_JP = {"Ari": "おひつじ", "Tau": "おうし", "Gem": "ふたご", "Can": "かに",
            "Leo": "しし", "Vir": "おとめ", "Lib": "てんびん", "Sco": "さそり",
            "Sag": "いて", "Cap": "やぎ", "Aqu": "みずがめ", "Pis": "うお"}
PHASE_JP = {"10s": "10代", "20s": "20代", "30s": "30代",
            "40s": "40代", "50s": "50代", "60s_plus": "60代以降"}


def _esc(s):
    return htmllib.escape(str(s))


def _calc_age(year, month, day, today_year=None, today_month=None, today_day=None):
    """現在の年齢を計算（誕生日が来ていれば加算）"""
    from datetime import date
    today = date.today()
    today_year = today_year or today.year
    today_month = today_month or today.month
    today_day = today_day or today.day
    age = today_year - year
    if (today_month, today_day) < (month, day):
        age -= 1
    return age


def _to_paras(text):
    """段落区切りの文字列を <p> タグに"""
    paras = [p.strip() for p in text.split("\n\n") if p.strip()]
    out = []
    for p in paras:
        # 段落内の改行は <br> ではなく削除（読みやすさのため）
        p = p.replace("\n", "")
        out.append(f'<p class="fr-body">{_esc(p)}</p>')
    return "".join(out)


def _section(num, title, body_text, cite):
    """1セクションのHTMLを生成"""
    return f"""<div class="fr-section">
  <h3 class="fr-sec-title">【{num}. {_esc(title)}】</h3>
  <div class="fr-sec-body">
    {_to_paras(body_text)}
  </div>
  <p class="fr-cite">✦ {_esc(cite)}</p>
</div>"""


def _age_section(age_text, age, phase):
    return f"""<div class="fr-section fr-age-section">
  <h3 class="fr-sec-title">【あなたの今のフェーズ】</h3>
  <div class="fr-sec-body">
    {_to_paras(age_text)}
  </div>
  <p class="fr-cite">✦ {_esc(PHASE_JP[phase])}（{age}歳）</p>
</div>"""


def generate_field_report_html(name, year, month, day, hour, minute, city,
                               lat=None, lng=None, tz_str="Asia/Tokyo",
                               sample=False):
    """3分野レポートHTML生成

    sample=True: 太陽セクションまで開示するサンプル版
    """
    # 出生時刻不明判定（12:00ぴったり）
    time_unknown = (not sample) and (hour == 12 and minute == 0)
    age = _calc_age(year, month, day)
    phase = age_to_phase(age)

    # 惑星計算
    if lat is not None and lng is not None:
        subject = AstrologicalSubject(
            name, year, month, day, hour, minute,
            lng=lng, lat=lat, tz_str=tz_str, online=False,
            houses_system_identifier="K",
        )
    else:
        subject = AstrologicalSubject(name, year, month, day, hour, minute,
                                      city=city, houses_system_identifier="K")

    def planet_info(p):
        return {"sign_key": p.quality if False else _sign_key_from_sign(p.sign),
                "sign_jp": SIGNS_JP[_sign_key_from_sign(p.sign)],
                "deg": p.position}

    # kerykeion の sign プロパティ → key 変換
    def _sign_key_from_sign(sign):
        # kerykeion sign は "Gem" "Can" など省略形を返す
        return sign[:3] if len(sign) >= 3 else sign

    p = {
        "Sun": subject.sun, "Moon": subject.moon, "Mercury": subject.mercury,
        "Venus": subject.venus, "Mars": subject.mars,
        "Jupiter": subject.jupiter, "Saturn": subject.saturn,
    }

    def info(pl):
        sk = _sign_key_from_sign(pl.sign)
        return {"sign_key": sk, "sign_jp": SIGNS_JP[sk], "deg": pl.position}

    sun, moon, mercury = info(p["Sun"]), info(p["Moon"]), info(p["Mercury"])
    venus, mars = info(p["Venus"]), info(p["Mars"])
    jupiter, saturn = info(p["Jupiter"]), info(p["Saturn"])

    asc_sk = _sign_key_from_sign(subject.first_house.sign)
    mc_sk = _sign_key_from_sign(subject.tenth_house.sign)
    asc_jp = SIGNS_JP[asc_sk]
    mc_jp = SIGNS_JP[mc_sk]

    sk, mk = sun["sign_key"], mars["sign_key"]
    vk, jk = venus["sign_key"], jupiter["sign_key"]
    moonk = moon["sign_key"]

    # 仕事章
    work_sec3 = ""
    if time_unknown:
        work_sec3 = """<div class="fr-section fr-note">
  <h3 class="fr-sec-title">【3. 天職の方向】</h3>
  <div class="fr-sec-body">
    <p class="fr-body">（出生時刻が不明のため、天頂(MC)の正確な算出ができません。出生時刻が分かる場合は、より精度の高い天職の方向が読み取れます。）</p>
  </div>
</div>"""
    else:
        work_sec3 = _section(3, "天職の方向", WORK_MC_VOCATION[mc_sk],
                             f"MC（天頂）　{mc_jp}座")

    work_push_text = WORK_SUN_PUSH[sk] + "\n\nこれまでも、これからも、あなたの働き方は、あなただけのもの。焦らず、自分のペースで——だから、続けていい。"
    chapter_work = f"""<div class="fr-chapter">
  <h2 class="fr-chap-title">💼 第1章　仕事・天職</h2>
  <div class="fr-chap-intro">
    <p class="fr-body">この章では、あなたの「働き方」「強みの出方」「社会的な天職」を読み解きます。仕事は人生の大きな比重を占めるからこそ、「向いていない方向に時間を使わない」ことが、何より大切です。あなたの星が示す方向を、ここで確かめてください。</p>
  </div>
  {_section(1, "あなたの仕事観の核", WORK_SUN_CORE[sk], f"太陽　{sun['sign_jp']}座 {sun['deg']:.1f}°")}
  {_section(2, "あなたが輝く場面", WORK_MARS_STYLE[mk], f"火星　{mars['sign_jp']}座 {mars['deg']:.1f}°")}
  {work_sec3}
  {_section(4, "仕事で気をつけたいクセ", WORK_SUN_CAUTION[sk], f"太陽　{sun['sign_jp']}座")}
  {_age_section(WORK_AGE_NOTE[phase], age, phase)}
  {_section(5, "あなたへ", work_push_text, f"太陽　{sun['sign_jp']}座")}
</div>"""

    money_push_text = MONEY_VENUS_PUSH[vk] + "\n\n長期で見たら、あなたなりの豊かさは必ず育っていきます。続けていることそのものが、未来のあなたへの最大の贈り物です。"
    chapter_money = f"""<div class="fr-chapter">
  <h2 class="fr-chap-title">💰 第2章　お金・豊かさ</h2>
  <div class="fr-chap-intro">
    <p class="fr-body">この章では、あなたの「お金との付き合い方」「豊かさの育て方」「お金で陥りやすいクセ」を読み解きます。お金の不安は、誰もが多かれ少なかれ抱えるテーマ。「自分にとってのお金の意味」が見えると、不安が「指針」に変わります。</p>
  </div>
  {_section(1, "あなたのお金の感覚", MONEY_VENUS_CORE[vk], f"金星　{venus['sign_jp']}座 {venus['deg']:.1f}°")}
  {_section(2, "何にお金を使うと心が満たされるか", MONEY_SPEND_STYLE[vk], f"金星　{venus['sign_jp']}座")}
  {_section(3, "どこを伸ばすと豊かになるか", MONEY_JUPITER_WEALTH[jk], f"木星　{jupiter['sign_jp']}座 {jupiter['deg']:.1f}°")}
  {_section(4, "お金で気をつけたいクセ", MONEY_VENUS_CAUTION[vk], f"金星　{venus['sign_jp']}座")}
  {_age_section(MONEY_AGE_NOTE[phase], age, phase)}
  {_section(5, "あなたへ", money_push_text, f"金星　{venus['sign_jp']}座／木星　{jupiter['sign_jp']}座")}
</div>"""

    love_push_text = LOVE_VENUS_PUSH[vk] + "\n\n「人と繋がる愛」と「自分自身を大切にする時間」——この両方を持てることが、あなたの愛の豊かさです。"
    chapter_love = f"""<div class="fr-chapter">
  <h2 class="fr-chap-title">🌹 第3章　恋愛・パートナーシップ</h2>
  <div class="fr-chap-intro">
    <p class="fr-body">この章では、あなたの「愛し方の核」「惹かれる相手」「本当に求める関係性」を読み解きます。恋愛・パートナーシップは、人生のどの段階でも形を変えながら続いていく営み。ここで読み解く愛のかたちが、これからの指針になります。</p>
  </div>
  {_section(1, "あなたの愛し方の核", LOVE_VENUS_CORE[vk], f"金星　{venus['sign_jp']}座 {venus['deg']:.1f}°")}
  {_section(2, "どんな人に心が動くか", LOVE_MARS_ATTRACTION[mk], f"火星　{mars['sign_jp']}座")}
  {_section(3, "求める関係性", LOVE_MOON_NEEDS[moonk], f"月　{moon['sign_jp']}座 {moon['deg']:.1f}°")}
  {_section(4, "恋愛で気をつけたいこと", LOVE_VENUS_CAUTION[vk], f"金星　{venus['sign_jp']}座／月　{moon['sign_jp']}座")}
  {_age_section(LOVE_AGE_NOTE[phase], age, phase)}
  {_section(5, "あなたへ", love_push_text, f"金星　{venus['sign_jp']}座")}
</div>"""

    synthesis = """<div class="fr-synthesis">
  <h2 class="fr-chap-title fr-chap-title-sub">🌟 3章を統合した「あなた」</h2>
  <div class="fr-chap-intro">
    <p class="fr-body">仕事・お金・恋愛——3つの分野は、それぞれ別の星が司っています。同じ「あなた」の中でも、分野ごとに使われている星が違うので、「仕事ではしっかり者なのに、恋愛では揺れる」といった矛盾は、矛盾ではなく自然な姿。</p>
    <p class="fr-body">仕事を司る太陽・火星・MC、お金を司る金星・木星、愛を司る金星・月・火星。それぞれの星があなたなりに動くことで、人生の3つの分野が形作られています。</p>
    <p class="fr-body">このレポートを、迷ったときに開いてください。3つの分野で「今、自分はどの星に動かされているか」を確かめると、混乱が「地図」に変わります。</p>
  </div>
</div>"""

    chart_summary = f"""<div class="fr-summary">
  <h2 class="fr-chap-title fr-chap-title-sub">🪐 あなたのチャート要約</h2>
  <p class="fr-summary-intro">このレポートは、以下の天体配置から読み解きました。</p>
  <table class="fr-summary-table">
    <tr><td>☉ 太陽</td><td>{sun['sign_jp']}座 {sun['deg']:.1f}°</td><td>仕事観の核</td></tr>
    <tr><td>☽ 月</td><td>{moon['sign_jp']}座 {moon['deg']:.1f}°</td><td>求める関係性</td></tr>
    <tr><td>☿ 水星</td><td>{mercury['sign_jp']}座 {mercury['deg']:.1f}°</td><td>思考・言葉</td></tr>
    <tr><td>♀ 金星</td><td>{venus['sign_jp']}座 {venus['deg']:.1f}°</td><td>愛とお金の感覚</td></tr>
    <tr><td>♂ 火星</td><td>{mars['sign_jp']}座 {mars['deg']:.1f}°</td><td>行動の燃料／惹かれる相手</td></tr>
    <tr><td>♃ 木星</td><td>{jupiter['sign_jp']}座 {jupiter['deg']:.1f}°</td><td>豊かさが育つ場所</td></tr>
    <tr><td>♄ 土星</td><td>{saturn['sign_jp']}座 {saturn['deg']:.1f}°</td><td>一生の学び</td></tr>
    <tr><td>ASC</td><td>{asc_jp}座</td><td>外向きの自分</td></tr>
    <tr><td>MC</td><td>{mc_jp}座</td><td>社会的な天職</td></tr>
  </table>
  <p class="fr-summary-note">このレポートで触れていない他の配置（細かいハウス、アスペクトなど）もあなたの一部です。より詳しい読み解きは、出生チャートレポートでご覧いただけます。</p>
</div>"""

    # サンプル版なら仕事章までで切る
    if sample:
        chapter_money_html = """<div class="fr-chapter fr-locked">
  <h2 class="fr-chap-title">💰 第2章　お金・豊かさ</h2>
  <div class="fr-lock-msg">
    <p>🔒 第2章はフル版でご覧いただけます。</p>
    <p>あなたのチャートに基づいて、お金との付き合い方、豊かさが育つ場所、お金で陥りやすいクセを読み解きます。</p>
  </div>
</div>"""
        chapter_love_html = """<div class="fr-chapter fr-locked">
  <h2 class="fr-chap-title">🌹 第3章　恋愛・パートナーシップ</h2>
  <div class="fr-lock-msg">
    <p>🔒 第3章はフル版でご覧いただけます。</p>
    <p>あなたの愛し方の核、惹かれる相手、本当に求める関係性を読み解きます。</p>
  </div>
</div>"""
    else:
        chapter_money_html = chapter_money
        chapter_love_html = chapter_love

    css = """<style>
:root {
  --bg: #FBF8F2;
  --gold: #B89858;
  --gold-d: #7A5018;
  --navy: #1C1A2E;
  --text: #1C1A2E;
  --text-m: #4A4860;
  --text-l: #7A6850;
  --cite: #9A8870;
  --panel: #FFFFFF;
  --border-l: #E8E0D0;
}
body { font-family: "Hiragino Mincho ProN", "ヒラギノ明朝 ProN W3", serif;
  color: var(--text); background: var(--bg); line-height: 1.85;
  font-size: 10pt; margin: 0; padding: 0; }
.fr-container { max-width: 760px; margin: 0 auto; padding: 24px; }
.fr-title { font-size: 22pt; text-align: center; color: var(--gold-d);
  letter-spacing: .04em; margin: 24px 0 8px; }
.fr-subtitle { text-align: center; font-size: 11pt; color: var(--text-l);
  font-style: italic; margin: 0 0 16px; }
.fr-intro { background: var(--panel); border: 1px solid var(--border-l);
  border-left: 4px solid var(--gold); padding: 16px 20px;
  margin: 0 0 32px; border-radius: 2px; }
.fr-intro p { margin: .5em 0; font-size: 10.5pt; }
.fr-chapter { margin: 0 0 32px; page-break-before: always; }
.fr-chapter:first-of-type { page-break-before: auto; }
.fr-chap-title { font-size: 16pt; color: var(--gold-d);
  border-top: 2px solid var(--gold); border-bottom: 2px solid var(--gold);
  padding: 12px 0; margin: 0 0 16px; text-align: center;
  letter-spacing: .04em; }
.fr-chap-title-sub { font-size: 14pt; border-top: 1px solid var(--gold);
  border-bottom: 1px solid var(--gold); }
.fr-chap-intro { background: rgba(184,152,88,.06); padding: 12px 18px;
  margin: 0 0 20px; border-radius: 2px; }
.fr-chap-intro p { font-size: 10pt; color: var(--text-m); margin: 0; }
.fr-section { margin: 0 0 16px; page-break-inside: avoid; }
.fr-sec-title { font-size: 12pt; color: var(--gold-d);
  margin: 16px 0 8px; padding-left: 8px;
  border-left: 3px solid var(--gold); }
.fr-sec-body { padding-left: 12px; }
.fr-body { font-size: 10.5pt; margin: .5em 0; line-height: 1.95;
  color: var(--text); }
.fr-cite { font-size: 8.5pt; color: var(--cite);
  margin: 8px 0 0 12px; font-style: italic; letter-spacing: .02em; }
.fr-age-section { background: rgba(184,152,88,.04);
  padding: 10px 16px; border-radius: 2px; }
.fr-synthesis { margin: 32px 0; page-break-before: always; }
.fr-summary { margin: 32px 0; page-break-before: always; }
.fr-summary-intro { font-size: 10pt; color: var(--text-m);
  margin: 0 0 12px; }
.fr-summary-table { width: 100%; border-collapse: collapse;
  font-family: "Menlo", "SF Mono", monospace; font-size: 10pt; }
.fr-summary-table td { padding: 4px 12px; border-bottom: 1px dashed var(--border-l); }
.fr-summary-table td:first-child { color: var(--gold-d); width: 60px; }
.fr-summary-table td:nth-child(2) { width: 200px; }
.fr-summary-table td:last-child { color: var(--text-l); font-style: italic; }
.fr-summary-note { font-size: 9.5pt; color: var(--text-l);
  margin: 16px 0 0; line-height: 1.6; }
.fr-locked { background: rgba(184,152,88,.06);
  padding: 24px; text-align: center; border-radius: 4px; }
.fr-lock-msg p { color: var(--text-m); margin: .5em 0; }
.fr-note { background: rgba(176,120,136,.06); padding: 12px 16px;
  border-radius: 2px; }
@media print {
  .fr-chapter, .fr-synthesis, .fr-summary, .fr-section { page-break-inside: avoid; }
}
</style>"""

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<title>仕事・お金・恋愛 — {_esc(name)}さんのレポート</title>
{css}
</head>
<body>
<div class="fr-container">
  <h1 class="fr-title">仕事・お金・恋愛 — あなたの3つの分野レポート</h1>
  <p class="fr-subtitle">{_esc(name)} さん</p>
  <div class="fr-intro">
    <p>このレポートは、人生の中で大きな比重を占める「仕事」「お金」「恋愛」の3つの分野について、あなたのチャートから読み解いた個別レポートです。</p>
    <p>仕事には仕事を司る星があり、お金にはお金を司る星があり、愛には愛を司る星があります。同じ「あなた」の中でも、分野ごとに使われている星が違うので、仕事ぶりと恋愛のスタイルが似ていないのは当然のこと。</p>
    <p>3章を通じて読むと、自分の中にある「複数の顔」が、矛盾ではなく豊かさだと感じられるはずです。</p>
  </div>
  {chapter_work}
  {chapter_money_html}
  {chapter_love_html}
  {synthesis}
  {chart_summary}
</div>
</body>
</html>"""


if __name__ == "__main__":
    # 夏紀さんで試運転
    html = generate_field_report_html(
        "夏紀", 1972, 6, 10, 22, 0, "新潟県十日町市",
        lat=37.13, lng=138.77,
    )
    out = os.path.expanduser("~/Documents/code_yousai/drafts/preview/夏紀さん_field_report_html.html")
    with open(out, "w") as f:
        f.write(html)
    print(f"OK → {out}")

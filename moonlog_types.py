# -*- coding: utf-8 -*-
"""moonlog タイプ診断
月星座から12タイプ（動物＋ペルソナ）を判定し、入口フォーム／結果ページのHTMLを返す。
app.py から import して /type・/type/result ルートで使う。
"""
import html as _html
import os
import markdown as _md
from moonlog_astrology import resolve_location
from kerykeion import AstrologicalSubject


def _esc(s):
    return _html.escape(str(s))


SIGN_JP = {
    "Ari": "牡羊座", "Tau": "牡牛座", "Gem": "双子座", "Can": "蟹座",
    "Leo": "獅子座", "Vir": "乙女座", "Lib": "天秤座", "Sco": "蠍座",
    "Sag": "射手座", "Cap": "山羊座", "Aqu": "水瓶座", "Pis": "魚座",
}

# 12タイプ（月星座キー → 動物・タイプ名・画像・説明・一言）
TYPE_DATA = {
    "Ari": {
        "animal": "柴犬", "img": "aries.png", "name": "まっすぐ走る",
        "desc": "感じたら、もう動いている。考えるより、心が先に反応します。新しいこと、まっさきに手を挙げるのも、たいていあなた。怒りはすぐ燃えて、すぐ消える。じっとしているのが少し苦手で、自分の速さに自分で疲れることもあるけれど、その裏表のなさが、まわりに風を起こします。",
        "hitokoto": "迷っているなら、それはもう答えが出ているサイン。最初の一歩を踏みだしてみて。",
    },
    "Tau": {
        "animal": "アルパカ", "img": "taurus.png", "name": "ゆったりマイペース",
        "desc": "ゆっくりが、ちょうどいい。急かされると、ペースを乱されて動けなくなるタイプです。穏やかで、一緒にいる人をほっとさせる人。決めるまでには時間がかかるけれど、決めたあとは揺らがない。それが、あなたの確かさです。",
        "hitokoto": "あなたのペースが、いちばん確かな道。あわてず、心地よい一歩から始めてみて。",
    },
    "Gem": {
        "animal": "リス", "img": "gemini.png", "name": "好奇心のままに動く",
        "desc": "興味がいつも、あちこちに動いています。新しいこと、知らない話、面白い人。「それ何?」と感じる瞬間が、いちばん生きている時間。気持ちを言葉にするのが上手で、人と人をつなぐのも自然にできます。たくさんのことに気を取られるのも、世界を広く受け取れる力です。",
        "hitokoto": "気になることがあるなら、それがあなたの次の入り口。軽い気持ちで、のぞいてみて。",
    },
    "Can": {
        "animal": "うさぎ", "img": "cancer.png", "name": "そっと包みこむ",
        "desc": "「守りたい」が、心の真ん中にいる人。居場所をつくるのが上手で、あなたのそばは、誰かにとっての帰る場所になっています。人の気持ちに敏感だから、知らないうちに空気を抱えこんで疲れることも。やさしさは、努力ではなく、生まれ持ったあなたの形です。",
        "hitokoto": "いつも誰かに向けている優しさを、ほんの少し、自分にも分けてあげて。",
    },
    "Leo": {
        "animal": "ライオン", "img": "leo.png", "name": "のびやかに輝く",
        "desc": "感情を、のびのびと表に出す人。あなたが楽しそうにしていると、まわりまで明るくなります。「見てもらえる」「認めてもらえる」と、ぐっと力が湧く。それは甘えではなく、輝くための栄養なんです。素直に「うれしい」が言えるのも、あなたの魅力。",
        "hitokoto": "心が動いたら、それを言葉や表情にのせてみて。あなたの輝きは、まわりへの贈りものです。",
    },
    "Vir": {
        "animal": "はりねずみ", "img": "virgo.png", "name": "ていねいに整える",
        "desc": "小さなことに、よく気がつく人。人が見落とすところに目が届き、ていねいに整える。役に立てると、ほっとする。ただ、自分にだけは厳しくて、「まだ足りない」と感じやすい。まわりから見れば、あなたはとっくに十分やっています。",
        "hitokoto": "「まだ足りない」と感じたら、いったん手を止めて。あなたのがんばりは、もう十分に届いています。",
    },
    "Lib": {
        "animal": "白鳥", "img": "libra.png", "name": "やわらかくつなぐ",
        "desc": "人と人のあいだに立って、空気をやわらかくする。対立が苦手で、みんなが気持ちよくいられるように、自然と気を配る人です。美しいもの・心地よい関係に、心が安らぐ。相手を立てすぎて、自分の気持ちを後回しにしてしまうのは、あなたの調和の力の裏返しです。",
        "hitokoto": "相手を思いやれるあなたへ。今度は「わたしはこうしたい」を、そっと口に出してみて。",
    },
    "Sco": {
        "animal": "オオカミ", "img": "scorpio.png", "name": "深く想う",
        "desc": "感情の振れ幅が、表より深くにある人。一度心を許した相手やことには、とことん。表にはあまり出さないけれど、内側には、静かで強い情熱が流れています。浅く広くより、ひとつの深いつながりを選ぶ。気持ちを抱えこみやすいから、信頼できる人にだけ、そっと開いていい。",
        "hitokoto": "胸の奥にしまった想いを、信じられる人にひとつ、打ち明けてみて。深い心は、預けても大丈夫。",
    },
    "Sag": {
        "animal": "ウマ", "img": "sagittarius.png", "name": "遠くを目指す",
        "desc": "心はいつも、まだ見ぬ場所のほうを向いています。新しい景色、知らない世界、まだ答えのない問い。そこに、心が伸びる。自由でいられるとき、いちばんあなたらしくいられる人。明るく前向きで、まわりの視野まで広げてくれる存在です。",
        "hitokoto": "心が遠くを向いたら、それは進んでいいというサイン。小さな冒険から、踏みだしてみて。",
    },
    "Cap": {
        "animal": "ヤギ", "img": "capricorn.png", "name": "一歩ずつ積みあげる",
        "desc": "こつこつと、時間をかけて、本物をつくる人。感情をすぐには出さず、静かに責任を引き受ける。派手な成果より、積みあげた確かさに価値を感じます。がんばり屋さんだからこそ、たまには「がんばらない自分」を、自分に許してあげていい。",
        "hitokoto": "がんばり続けてきたあなたへ。今日は、背負っているものをひとつ、おろしてみて。",
    },
    "Aqu": {
        "animal": "ふくろう", "img": "aquarius.png", "name": "自分の道をゆく",
        "desc": "みんなと同じでなくていい。心のどこかで、そう知っている人。少し距離をとって眺めることで、自分らしさと自由を保っている。独自の視点があって、それが新しい風を運ぶ。「変わってる」は、欠点ではなく、自分の軌道を回っている証拠です。",
        "hitokoto": "「みんなと違う」と感じる選択こそ、あなたの道。ためらわず、そちらへ進んでみて。",
    },
    "Pis": {
        "animal": "シカ", "img": "pisces.png", "name": "人の気持ちに寄りそう",
        "desc": "人の気持ちを、自分のことのように感じ取れる人。共感が深く、やさしく、想像力がゆたか。誰かにそっと寄り添えるのは、まれな才能です。境界がやわらかいから、人の感情を受け取りすぎて疲れることも。ひとりで心を休める時間を、ちゃんと持っていい。",
        "hitokoto": "人の気持ちでいっぱいになったら、少しだけ、ひとりに戻る時間を。やさしさは、休んでも消えません。",
    },
}

# === もっと深く 8セクション（無料）— data/type_deep.md を読み込む ===
_DEEP_PATH = os.path.join(os.path.dirname(__file__), "data", "type_deep.md")
_SIGN_FROM_LABEL = {
    "牡羊座": "Ari", "牡牛座": "Tau", "双子座": "Gem", "蟹座": "Can",
    "獅子座": "Leo", "乙女座": "Vir", "天秤座": "Lib", "蠍座": "Sco",
    "射手座": "Sag", "山羊座": "Cap", "水瓶座": "Aqu", "魚座": "Pis",
}


def _load_deep():
    """data/type_deep.md を読み、各タイプ本文を HTML 化してサインキー別に返す。"""
    try:
        text = open(_DEEP_PATH, encoding="utf-8").read()
    except Exception:
        return {}
    if text.startswith("---"):  # YAML frontmatter
        text = text.split("---", 2)[2]
    chunks = [c.strip() for c in text.split("\n---\n") if c.strip()]
    out = {}
    md = _md.Markdown(extensions=["extra", "nl2br"])
    for ch in chunks[1:]:  # 先頭は intro なので飛ばす
        lines = ch.split("\n")
        title = lines[0].lstrip("# ").strip()
        body = "\n".join(lines[1:]).strip()
        sign_key = None
        for jp, key in _SIGN_FROM_LABEL.items():
            if jp in title:
                sign_key = key
                break
        if not sign_key:
            continue
        md.reset()
        out[sign_key] = md.convert(body)
    return out


TYPE_DEEP = _load_deep()


_CSS = """
:root{--cream:#faf6ec;--card:#fffdf7;--navy:#22324f;--navy-d:#1a2740;
      --gold:#bd9a48;--ink:#3f4456;--soft:#7b7a72;}
*{box-sizing:border-box;margin:0;padding:0}
body{background:#ece6d8;color:var(--ink);
     font-family:"Hiragino Sans","Yu Gothic",sans-serif;line-height:1.9;
     padding:30px 14px 80px;}
.wrap{max-width:480px;margin:0 auto;background:var(--cream);
      border-radius:20px;overflow:hidden;
      box-shadow:0 14px 40px rgba(40,40,60,.16);}
.pad{padding:32px 28px 38px;}
.brand{text-align:center;font-size:14px;letter-spacing:.22em;color:var(--navy);
       margin-bottom:22px;}
.brand a{color:var(--navy);text-decoration:none;}
.q-title{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;
         font-size:21px;color:var(--navy-d);text-align:center;margin-bottom:6px;}
.q-sub{text-align:center;font-size:13px;color:var(--soft);margin-bottom:24px;}
.field{margin-bottom:16px;}
.field label{font-size:12px;color:var(--soft);display:block;margin-bottom:5px;}
.field input{width:100%;background:#fff;border:1px solid #ddd3bb;border-radius:10px;
             padding:12px 13px;font-size:15px;color:var(--navy-d);
             font-family:inherit;}
.hint{font-size:11px;color:#a59f90;margin-top:4px;}
.btn{display:block;width:100%;text-align:center;background:var(--navy);color:#f5ecd2;
     border:0;border-radius:30px;padding:15px;font-size:15px;letter-spacing:.08em;
     margin-top:24px;text-decoration:none;cursor:pointer;font-family:inherit;}
.label{text-align:center;font-size:12px;letter-spacing:.24em;color:var(--gold);
       margin-bottom:14px;}
.emblem{text-align:center;margin-bottom:12px;}
.emblem img{width:240px;height:240px;}
.persona{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;
         font-size:29px;color:var(--navy-d);text-align:center;line-height:1.4;}
.sub{text-align:center;font-size:13px;color:var(--soft);
     margin:8px 0 26px;letter-spacing:.06em;}
.revelation{background:var(--navy);color:#f1e8d2;border-radius:16px;
            padding:22px;margin-bottom:24px;}
.rev-title{font-size:12px;letter-spacing:.2em;color:var(--gold);
           text-align:center;margin-bottom:12px;}
.revelation p{font-size:14.5px;}
.revelation b{color:#fff;}
.desc{font-size:14.5px;margin-bottom:24px;}
.hitokoto{border:1.5px solid var(--gold);border-radius:16px;
          padding:20px 22px;margin-bottom:30px;background:#fffefa;}
.h-label{font-size:12px;letter-spacing:.16em;color:var(--gold);
         text-align:center;margin-bottom:10px;}
.hitokoto p{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;
            font-size:16px;color:var(--navy-d);text-align:center;line-height:1.9;}
.divider{text-align:center;font-size:11px;color:#aaa391;letter-spacing:.16em;
         border-top:1px dashed #cfc7af;padding-top:16px;margin-bottom:20px;}
.more-box{background:#fff;border:1px solid #e3dcc6;border-radius:14px;
          padding:22px 22px 24px;}
.more-title{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;
            font-size:17px;color:var(--navy-d);text-align:center;margin-bottom:6px;}
.more-lead{text-align:center;font-size:12.5px;color:var(--soft);margin-bottom:4px;}
.more-list{list-style:none;margin:10px 0 0;padding:0;}
.more-list li{font-size:13.5px;color:var(--navy);padding:10px 2px;
              border-bottom:1px solid #f0ead8;}
.more-list li:last-child{border-bottom:0;}
.more-list li::before{content:"✦　";color:var(--gold);}
.cta{display:block;text-align:center;background:var(--gold);color:#fff;
     border-radius:30px;padding:15px;font-size:14.5px;letter-spacing:.04em;
     text-decoration:none;margin-top:18px;}
.cta small{display:block;font-size:11px;opacity:.85;letter-spacing:0;margin-top:2px;}
.again{text-align:center;margin-top:20px;}
.again a{color:var(--soft);font-size:12px;text-decoration:none;}
.errbox{background:#fff4f0;border:1px solid #e7c3b3;border-radius:12px;
        padding:18px;color:#9a5a44;font-size:14px;text-align:center;}
.type-deep{margin-top:4px;}
.type-deep h2{font-family:"Hiragino Mincho ProN","Yu Mincho",serif;
              font-size:17px;color:var(--navy-d);margin:32px 0 10px;
              padding:0 0 6px;border-bottom:1px solid #e3dcc6;}
.type-deep h2:first-child{margin-top:6px;}
.type-deep p{font-size:14.5px;margin:10px 0;line-height:1.95;}
.type-deep ul{list-style:none;padding:0;margin:8px 0;}
.type-deep ul li{font-size:14.5px;padding:4px 0;line-height:1.85;}
.type-deep ul li::before{content:"・";color:var(--gold);margin-right:6px;}
.type-deep ol{padding-left:1.4em;margin:10px 0;}
.type-deep ol li{font-size:14.5px;line-height:1.95;margin:8px 0;}
.type-deep strong{color:var(--navy-d);}
"""


def _page(title, body):
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(title)}</title>
<style>{_CSS}</style>
</head>
<body>
<div class="wrap"><div class="pad">
{body}
</div></div>
</body>
</html>"""


def render_input_page():
    """タイプ診断の入口フォーム"""
    body = """
  <div class="brand">🌙 <a href="/">moonlog</a></div>
  <div class="q-title">あなたのタイプを調べる</div>
  <div class="q-sub">生まれた瞬間の月から、素のあなたを読み解きます</div>
  <div style="background:#f5f1e3;border-left:3px solid #bd9a48;padding:11px 14px;font-size:12.5px;color:#3f4456;line-height:1.85;margin-bottom:22px;border-radius:0 6px 6px 0;">
    雑誌などの星座は <b>太陽星座</b>（社会的な顔）。月タイプ診断は <b>月星座</b>（心の奥・素の自分）からタイプを判定します。<br>
    <a href="/blog/taiyou-to-tsuki-no-chigai" target="_blank" style="color:#bd9a48;text-decoration:underline;">→ 太陽星座と月星座の違いを読む</a>
  </div>
  <form method="post" action="/type/result">
    <div class="field">
      <label>生年月日</label>
      <input type="date" name="birthdate" required>
    </div>
    <div class="field">
      <label>出生時刻</label>
      <input type="time" name="birthtime">
      <div class="hint">わからなければ空欄でOK（その場合は昼12時で計算します）</div>
    </div>
    <div class="field">
      <label>出生地</label>
      <input type="text" name="city" value="東京" required>
    </div>
    <button type="submit" class="btn">あなたのタイプを見る</button>
  </form>
  <div class="again"><a href="/">← moonlog トップへ戻る</a></div>
"""
    return _page("月タイプ診断 ｜ moonlog", body)


def _err_page(msg):
    body = f"""
  <div class="brand">🌙 <a href="/">moonlog</a></div>
  <div class="errbox">{_esc(msg)}</div>
  <div class="again"><a href="/type">← もう一度入力する</a></div>
"""
    return _page("月タイプ診断 ｜ moonlog", body)


def compute_type(year, month, day, hour, minute, city,
                 lat=None, lng=None, tz=None):
    """出生データから (月星座キー, 太陽星座キー) を返す。
    lat/lng が渡されればそれを使い、なければ city から解決する。"""
    if lat is None or lng is None:
        lat, lng, tz = resolve_location(city)
    if not tz:
        tz = "Asia/Tokyo"
    subj = AstrologicalSubject(
        "type", year, month, day, hour, minute,
        lng=lng, lat=lat, tz_str=tz, online=False,
        houses_system_identifier="K",
    )
    return subj.moon.sign, subj.sun.sign


def render_result_page(moon_key, sun_key, birth_data=None):
    """月星座キー・太陽星座キーから結果ページを返す。
    birth_data: {"name","year","month","day","hour","minute","city","lat","lng"}
                を渡すと、体験版への引き継ぎ用 hidden form を生成する。"""
    t = TYPE_DATA.get(moon_key)
    if not t:
        return _err_page("タイプの判定に失敗しました。お手数ですが、もう一度お試しください。")

    moon_jp = SIGN_JP.get(moon_key, moon_key)
    # 注：sun_key は計算するが、タイプ診断は月のみのスコープなので表示には使わない

    rev = (f'<p>あなたの月は、<b>{_esc(moon_jp)}</b>。</p>'
           f'<p>「{_esc(t["name"])}」は、生まれた瞬間の月の位置から導いた、'
           f'あなたの素顔——内側の自分です。</p>')

    # 体験版へ引き継ぎ用 hidden form（birth_data があれば）
    preview_form = ""
    preview_step = ""
    if birth_data:
        bd = birth_data
        hidden_inputs = "".join(
            f'<input type="hidden" name="{k}" value="{_esc(v)}">'
            for k, v in bd.items() if v is not None and v != ""
        )
        preview_form = f'''
  <form id="to-preview" method="post" action="/preview" target="_blank" style="display:none;">
    {hidden_inputs}
  </form>'''
        preview_step = f'''
  <div class="divider">― もう少し読みたいなら ―</div>
  <a href="#" onclick="event.preventDefault();document.getElementById('to-preview').submit();return false;"
     style="display:block;background:#fff8e7;border:1.5px solid #bd9a48;border-radius:14px;padding:20px 22px;text-align:center;text-decoration:none;color:#1a2740;margin-bottom:26px;">
    <div style="font-family:'Hiragino Mincho ProN','Yu Mincho',serif;font-size:16px;color:#1a2740;margin-bottom:4px;">続けて、太陽・月のレポートを読む</div>
    <div style="font-size:12px;color:#7b7a72;">あなたの太陽と月を文章でじっくり ／ 無料・再入力不要</div>
    <div style="font-size:13px;color:#bd9a48;margin-top:8px;font-weight:600;">→ 体験版を読む</div>
  </a>'''

    body = f"""
  <div class="brand">🌙 <a href="/">moonlog</a></div>
  <div class="label">Y O U R　T Y P E</div>
  <div class="emblem"><img src="/static/images/types/final/{_esc(t['img'])}" alt="{_esc(t['animal'])}"></div>
  <div class="persona">{_esc(t['name'])}</div>
  <div class="sub">{_esc(moon_jp)}の月 ・ {_esc(t['animal'])}</div>
  <div style="text-align:center;font-size:11.5px;color:#7b7a72;margin:-14px 0 22px;letter-spacing:.02em;">
    ※ 雑誌などの星座は太陽星座。これは「もう一つのあなたの星座」＝月星座から判定しています。
    <a href="/blog/taiyou-to-tsuki-no-chigai" target="_blank" style="color:#bd9a48;text-decoration:underline;">違いを読む →</a>
  </div>

  <div class="revelation">
    <div class="rev-title">あ な た の 月</div>
    {rev}
  </div>

  <div class="desc">{_esc(t['desc'])}</div>

  <div class="hitokoto">
    <div class="h-label">― あなたへの一言 ―</div>
    <p>{_esc(t['hitokoto'])}</p>
  </div>

  <div class="divider">― 「{_esc(t['name'])}」を、もっと深く ―</div>
  <div class="type-deep">{TYPE_DEEP.get(moon_key, '')}</div>
{preview_form}{preview_step}
  <div class="divider">― 次の世界へ ―</div>
  <div class="more-box">
    <div class="more-title">あなたの全体像を、7つの星で</div>
    <p class="more-lead">月タイプ診断は、生まれた瞬間の月を動物のタイプで。出生チャートは7つの星と第一印象の星（アセンダント）を文章でじっくり読む、もう一つの“あなたという地図”です。同じ月も、別の角度から読みます。</p>
    <ul class="more-list">
      <li>太陽 ― 社会で見せる、あなたの顔</li>
      <li>月 ― 感情と内面（チャート全体の中で）</li>
      <li>水星 ― 思考とコミュニケーション</li>
      <li>金星 ― 愛し方と喜びの感じ方</li>
      <li>火星 ― 情熱と行動のエネルギー</li>
      <li>木星 ― 発展と幸運のパターン</li>
      <li>土星 ― 魂の課題と学び</li>
      <li>アセンダント ― まわりから見えるあなた</li>
    </ul>
    <a class="cta" href="/#form-section">出生チャート（フル版）を読む<small>あなたという地図、ぜんぶ ／ ¥980</small></a>
  </div>

  <div class="again"><a href="/type">← もう一度、別の生年月日で調べる</a></div>
"""
    return _page(f"あなたは「{t['name']}」｜ moonlog 月タイプ診断", body)

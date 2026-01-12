import os
import sys
import requests
from datetime import datetime, timedelta
from deep_translator import GoogleTranslator

# =====================
# 環境変数
# =====================
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

if not WEBHOOK_URL or not NEWS_API_KEY:
    sys.exit("ERROR: Environment variables not set")

# =====================
# 時刻判定
# =====================
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)
weekday = now_jst.weekday()  # 月曜=0, 日曜=6

if weekday == 5:  # 土曜はスキップ
    sys.exit("Saturday skipped")
MODE = "REVIEW" if now_utc.hour != 9 else "SCENARIO"  # 6:00 JST = REVIEW, 18:00 JST = SCENARIO

translator = GoogleTranslator(source="en", target="ja")

# =====================
# NewsAPI取得
# =====================
def fetch_news(query, from_dt, to_dt, size):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "from": from_dt,
        "to": to_dt,
        "pageSize": size,
        "apiKey": NEWS_API_KEY,
    }
    res = requests.get(url, params=params).json()
    return res.get("articles", [])

def fmt(a, mark):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))
    dt = datetime.fromisoformat(a["publishedAt"].replace("Z","")) + timedelta(hours=9)
    return f"{mark}【{dt:%Y/%m/%d %H:%M JST}】{title}\n{desc}\n"

# =====================
# ニュース構築
# =====================
def build_news():
    blocks = []

    # ---------- 前日の影響 ----------
    back_days = 3 if weekday == 0 else 1
    impact = fetch_news(
        query="US stocks market reaction earnings Fed semiconductor",
        from_dt=(now_utc - timedelta(days=back_days)).strftime("%Y-%m-%d"),
        to_dt=now_utc.strftime("%Y-%m-%d"),
        size=5,
    )
    block = "【ニュース｜前日の影響評価】\n"
    if impact:
        for a in impact:
            block += fmt(a, "★")
            block += "▶ 株価・出来高・指数比較で影響度を評価\n\n"
    else:
        block += "※ 株価に直接影響した明確な材料は限定的\n\n"
    blocks.append(block)

    # ---------- 最新（速報） ----------
    latest = fetch_news(
        query="US market Fed comments semiconductor NVDA AMD",
        from_dt=(now_utc - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S"),
        to_dt=now_utc.strftime("%Y-%m-%dT%H:%M:%S"),
        size=3,
    )
    block = "【ニュース｜最新（速報）】\n"
    if latest:
        for a in latest:
            block += fmt(a, "・")
            block += "▶ 市場反応はこれから\n\n"
    else:
        block += "※ 目立った速報ニュースなし\n\n"
    blocks.append(block)

    # ---------- トレンド（1週間） ----------
    trend = fetch_news(
        query="Federal Reserve policy semiconductor earnings NVDA geopolitics US",
        from_dt=(now_utc - timedelta(days=7)).strftime("%Y-%m-%d"),
        to_dt=now_utc.strftime("%Y-%m-%d"),
        size=3,
    )
    block = "【トレンドを形成している大きな材料（過去1週間）】\n"
    if trend:
        for a in trend:
            block += fmt(a, "◆")
            block += "▶ 現在の中期トレンドに影響\n\n"
    else:
        block += "※ トレンドはテクニカル主導\n\n"
    blocks.append(block)

    # ---------- NVDA個別 ----------
    nvda = fetch_news(
        query="NVDA semiconductor earnings guidance",
        from_dt=(now_utc - timedelta(days=3)).strftime("%Y-%m-%d"),
        to_dt=now_utc.strftime("%Y-%m-%d"),
        size=3,
    )
    block = "【NVDA 個別動向】\n"
    if nvda:
        for a in nvda:
            block += fmt(a, "・")
            block += "▶ 出来高・高値圏・押し目での反応を評価\n\n"
    else:
        block += "※ 特筆すべき個別動向なし\n\n"
    blocks.append(block)

    # ---------- 米国政治・政治家発言 ----------
    politics = fetch_news(
        query="US politics Fed Congress President semiconductor",
        from_dt=(now_utc - timedelta(days=3)).strftime("%Y-%m-%d"),
        to_dt=now_utc.strftime("%Y-%m-%d"),
        size=3,
    )
    block = "【米国政治・政治家発言】\n"
    if politics:
        for a in politics:
            block += fmt(a, "・")
            block += "▶ 市場反応はまだ限定的／背景として注視\n\n"
    else:
        block += "※ 特筆すべき発言なし\n\n"
    blocks.append(block)

    return "\n".join(blocks)

# =====================
# テクニカル
# =====================
def technical_section():
    if MODE == "SCENARIO":
        return (
            "【テクニカル状況】\n"
            "・NASDAQは20EMA上を維持\n"
            "・高値圏での持ち合い\n"
            "・出来高は低下傾向\n\n"
            "【半導体】\n"
            "・SOX指数はNASDAQより相対的に強い\n"
            "・NVDAは押し目形成、AMDはレンジ上限試し\n\n"
            "【本日のシナリオ】\n"
            "・材料＋出来高 → 上方向ブレイク（A）\n"
            "・調整優勢 → 利確・押し目（B）\n"
            "・崩れ → 下抜けリスク（C）\n"
        )
    else:
        return (
            "【実際の値動き】\n"
            "・出来高を伴うブレイクの有無\n"
            "・前日高値／安値の攻防\n\n"
            "【半導体の反応】\n"
            "・NVDAが指数を上回ったか\n"
            "・SOXがトレンド維持できたか\n\n"
            "【検証】\n"
            "・効いたニュース（★）と効かなかった材料を整理\n"
        )

# =====================
# メッセージ生成
# =====================
title = "【米国株 市場シナリオ】18:00 JST" if MODE=="SCENARIO" else "【米国株 市場レビュー】6:00 JST"

message = (
    "━━━━━━━━━━━━━━━━━━\n"
    f"{title}\n"
    "（米国株 / 半導体中心）\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    f"{build_news()}\n"
    f"{technical_section()}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻：{now_jst:%Y-%m-%d %H:%M JST}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

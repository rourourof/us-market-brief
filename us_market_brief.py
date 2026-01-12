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
# 時刻（UTC / JST）
# =====================
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)

# =====================
# モード判定（UTC基準で確定）
# =====================
# 09:00 UTC → 18:00 JST → SCENARIO
# 21:00 UTC → 06:00 JST → REVIEW
if now_utc.hour == 9:
    MODE = "SCENARIO"
elif now_utc.hour == 21:
    MODE = "REVIEW"
else:
    MODE = "REVIEW"  # 手動実行用

# =====================
# ニュース取得（期間指定あり）
# =====================
def fetch_news():
    url = "https://newsapi.org/v2/everything"

    if MODE == "REVIEW":
        from_date = (now_utc - timedelta(days=1)).strftime("%Y-%m-%d")
        to_date = now_utc.strftime("%Y-%m-%d")
    else:
        from_date = (now_utc - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        to_date = now_utc.strftime("%Y-%m-%dT%H:%M:%S")

    params = {
        "q": "US stock market semiconductor NVDA AMD Federal Reserve politics",
        "language": "en",
        "sortBy": "publishedAt",
        "from": from_date,
        "to": to_date,
        "pageSize": 5,
        "apiKey": NEWS_API_KEY,
    }

    res = requests.get(url, params=params).json()
    return res.get("articles", [])

translator = GoogleTranslator(source="en", target="ja")

# =====================
# ニュース整形
# =====================
def build_news_section():
    articles = fetch_news()

    if not articles:
        return "※ 対象期間内の新規ニュースは限定的\n"

    blocks = []

    for a in articles:
        title = translator.translate(a.get("title", ""))
        desc = translator.translate(a.get("description", ""))

        published = a.get("publishedAt")
        dt = datetime.fromisoformat(published.replace("Z", "")) + timedelta(hours=9)
        date_str = dt.strftime("%Y/%m/%d %H:%M JST")

        mark = "★" if MODE == "REVIEW" else "・"

        block = (
            f"{mark}【{date_str}】{title}\n"
            f"{desc}\n"
        )
        blocks.append(block)

    return "\n".join(blocks)

# =====================
# テクニカル文章
# =====================
def technical_section():
    if MODE == "SCENARIO":
        return (
            "【テクニカル状況】\n"
            "・NASDAQは20EMA上を維持\n"
            "・高値圏での持ち合い\n"
            "・出来高は低下し材料待ち\n\n"
            "【半導体】\n"
            "・SOX指数はNASDAQより強含み\n"
            "・NVDAは押し目形成\n\n"
            "【想定シナリオ】\n"
            "・材料＋出来高 → 上放れ\n"
            "・反応薄 → 調整継続\n"
        )
    else:
        return (
            "【実際の値動き】\n"
            "・出来高を伴うブレイクの有無を確認\n\n"
            "【半導体の反応】\n"
            "・NVDAが指数を上回れば材料集中\n\n"
            "【検証】\n"
            "・ニュースが効いたか／織り込み済みかを判定\n"
        )

# =====================
# メッセージ
# =====================
title = (
    "【米国株 市場シナリオ】18:00 JST"
    if MODE == "SCENARIO"
    else "【米国株 市場レビュー】6:00 JST"
)

message = (
    "━━━━━━━━━━━━━━━━━━\n"
    f"{title}\n"
    "（米国株 / 半導体中心）\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "【ニュース】\n"
    f"{build_news_section()}\n\n"
    f"{technical_section()}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻：{now_jst.strftime('%Y-%m-%d %H:%M JST')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

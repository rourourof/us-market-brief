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
# JST 時刻
# =====================
now_jst = datetime.utcnow() + timedelta(hours=9)

translator = GoogleTranslator(source="en", target="ja")

# =====================
# ニュース取得 共通関数
# =====================
def fetch_news(query, size=3):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": size,
        "apiKey": NEWS_API_KEY,
    }
    return requests.get(url, params=params).json().get("articles", [])

# =====================
# ① 市場全体ニュース
# =====================
market_blocks = []

for a in fetch_news(
    "US stock market Federal Reserve inflation interest rate", 3
):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))

    published_utc = a.get("publishedAt")
    if published_utc:
        published = (
            datetime.fromisoformat(published_utc.replace("Z", ""))
            + timedelta(hours=9)
        ).strftime("%Y/%m/%d %H:%M JST")
    else:
        published = "日時不明"

    market_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【内容】{desc}\n\n"
        "【市場の受け止め】\n"
        "・金融政策や金利見通しへの連想が意識された\n\n"
        "【株価への影響】\n"
        "・NASDAQを中心に方向感が出やすい一日\n"
    )

# =====================
# ② 半導体セクター
# =====================
semi_blocks = []

for a in fetch_news(
    "NVIDIA AMD semiconductor chip US stock", 3
):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))

    published_utc = a.get("publishedAt")
    if published_utc:
        published = (
            datetime.fromisoformat(published_utc.replace("Z", ""))
            + timedelta(hours=9)
        ).strftime("%Y/%m/%d %H:%M JST")
    else:
        published = "日時不明"

    semi_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【内容】{desc}\n\n"
        "【セクターの受け止め】\n"
        "・AI投資、設備投資、需給見通しが意識された\n"
        "・NVDA、AMDなど主力株に連想が波及\n\n"
        "【株価への影響】\n"
        "・半導体株は指数より値動きが大きくなりやすい\n"
        "・SOX指数はNASDAQの先行指標として注目\n"
    )

# =====================
# メッセージ統合
# =====================
message = (
    "━━━━━━━━━━━━━━━━━━\n"
    "【米国株式市場ブリーフ】\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    "① 前日のニュースと市場全体への影響\n\n"
    + "\n".join(market_blocks)
    + "\n━━━━━━━━━━━━━━━━━━\n\n"
    "② 半導体セクター動向\n\n"
    + "\n".join(semi_blocks)
    + "\n━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

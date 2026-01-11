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
# 時刻（JST）
# =====================
now_jst = datetime.utcnow() + timedelta(hours=9)

# =====================
# ニュース取得（本文あり）
# =====================
def fetch_news():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "US stock market Federal Reserve inflation interest rate",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 3,
        "apiKey": NEWS_API_KEY,
    }
    return requests.get(url, params=params).json().get("articles", [])

translator = GoogleTranslator(source="en", target="ja")

news_blocks = []

for a in fetch_news():
    title = translator.translate(a.get("title", ""))
    description = translator.translate(a.get("description", ""))

    block = (
        f"● {title}\n"
        f"【内容】{description}\n"
        "【市場の受け止め】\n"
        "・金利や金融政策への連想が意識されやすい材料\n"
        "・ハイテク・成長株は反応しやすい\n"
        "【株価への影響】\n"
        "・NASDAQ中心に方向感が出やすい展開\n"
    )
    news_blocks.append(block)

# =====================
# メッセージ
# =====================
message = (
    "━━━━━━━━━━━━━━━━━━\n"
    "【米国株式市場ブリーフ】\n"
    "① 前日のニュースと株価への影響\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    + "\n".join(news_blocks) +
    "\n━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

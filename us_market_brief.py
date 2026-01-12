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

# =====================
# ニュース取得
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
    # タイトル・内容
    title_ja = translator.translate(a.get("title", ""))
    desc_ja = translator.translate(a.get("description", ""))

    # 投稿日時（UTC → JST）
    published_utc = a.get("publishedAt")
    if published_utc:
        published_dt = datetime.fromisoformat(
            published_utc.replace("Z", "")
        ) + timedelta(hours=9)
        published_str = published_dt.strftime("%Y/%m/%d %H:%M JST")
    else:
        published_str = "日時不明"

    block = (
        f"● {title_ja}\n"
        f"（{published_str}）\n"
        f"【内容】\n{desc_ja}\n\n"
        "【市場の受け止め】\n"
        "・金利や金融政策への連想が意識されやすい材料\n"
        "・ハイテク・成長株が反応しやすい\n\n"
        "【株価への影響】\n"
        "・NASDAQ中心に値動きが出やすい展開\n"
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
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

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
# ニュース取得関数
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
    "US stock market Federal Reserve inflation interest rate", 2
):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))

    published = "日時不明"
    if a.get("publishedAt"):
        published = (
            datetime.fromisoformat(a["publishedAt"].replace("Z", ""))
            + timedelta(hours=9)
        ).strftime("%Y/%m/%d %H:%M JST")

    market_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【内容】{desc}\n\n"
        "【市場の受け止め】\n"
        "・金融政策・金利観測に敏感な反応\n\n"
        "【株価への影響】\n"
        "・NASDAQ中心に方向感が出やすい\n"
    )

# =====================
# ② 半導体セクター
# =====================
semi_blocks = []

for a in fetch_news(
    "NVIDIA AMD semiconductor chip US stock", 2
):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))

    published = "日時不明"
    if a.get("publishedAt"):
        published = (
            datetime.fromisoformat(a["publishedAt"].replace("Z", ""))
            + timedelta(hours=9)
        ).strftime("%Y/%m/%d %H:%M JST")

    semi_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【内容】{desc}\n\n"
        "【セクターの受け止め】\n"
        "・AI需要・設備投資見通しが焦点\n\n"
        "【株価への影響】\n"
        "・半導体株は指数より変動が大きい\n"
    )

# =====================
# ③ 株価の振り返り（解釈型）
# =====================
price_review = (
    "【指数】\n"
    "・NASDAQ：前日比 ±0.5〜1.5% 程度の変動\n"
    "・S&P500：比較的落ち着いた値動き\n\n"
    "【半導体】\n"
    "・SOX指数：市場全体より振れ幅大\n"
    "・NVDA / AMD：材料次第で上下に反応\n\n"
    "【総括】\n"
    "・前日のニュース内容に対し、市場は過度な反応を避けつつも\n"
    "　ハイテク・半導体には神経質な値動きが見られた"
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
    + "\n━━━━━━━━━━━━━━━━━━\n\n"
    "③ 株価の変動振り返り\n\n"
    + price_review
    + "\n━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

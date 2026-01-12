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
weekday = now_jst.weekday()

# 土曜は配信しない
if weekday == 5:
    sys.exit(0)

translator = GoogleTranslator(source="en", target="ja")

# =====================
# ニュース取得関数
# =====================
def fetch_news(query, size=2):
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
# 共通：記事整形
# =====================
def format_article(a):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))

    published = "日時不明"
    if a.get("publishedAt"):
        published = (
            datetime.fromisoformat(a["publishedAt"].replace("Z", ""))
            + timedelta(hours=9)
        ).strftime("%Y/%m/%d %H:%M JST")

    return title, desc, published

# =====================
# ① 市場全体
# =====================
market_blocks = []
for a in fetch_news(
    "US stock market Federal Reserve inflation interest rate", 2
):
    title, desc, published = format_article(a)
    market_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【内容】{desc}\n\n"
        "【市場の受け止め】\n"
        "・金融政策や金利見通しを巡り慎重な解釈\n\n"
        "【株価への影響】\n"
        "・NASDAQ中心に方向感を探る動き\n"
    )

# =====================
# ② 半導体セクター
# =====================
semi_blocks = []
for a in fetch_news(
    "NVIDIA AMD semiconductor chip US stock", 2
):
    title, desc, published = format_article(a)
    semi_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【内容】{desc}\n\n"
        "【セクターの受け止め】\n"
        "・AI需要、設備投資、規制動向が意識された\n\n"
        "【株価への影響】\n"
        "・半導体株は指数より値動きが大きい\n"
    )

# =====================
# ③ 株価の振り返り
# =====================
price_review = (
    "【指数】\n"
    "・NASDAQ：ハイテク中心に変動\n"
    "・S&P500：比較的落ち着いた動き\n\n"
    "【半導体】\n"
    "・SOX指数：ニュース感応度が高い\n"
    "・NVDA / AMD：材料次第で上下\n\n"
    "【総括】\n"
    "・前日の材料に対し、市場は慎重ながらも\n"
    "　テーマ株には明確な反応が見られた"
)

# =====================
# ④ 米国政治・政治家の発言
# =====================
politics_blocks = []
for a in fetch_news(
    "US politics Biden Trump Congress Federal Reserve regulation", 2
):
    title, desc, published = format_article(a)
    politics_blocks.append(
        f"● {title}\n"
        f"（{published}）\n"
        f"【発言・動き】{desc}\n\n"
        "【市場の受け止め】\n"
        "・規制、財政、金融政策への影響を警戒\n\n"
        "【株価への影響】\n"
        "・ハイテク・半導体株は政策リスクに敏感\n"
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
    + "\n━━━━━━━━━━━━━━━━━━\n\n"
    "④ 米国政治・政治家の発言と市場影響\n\n"
    + "\n".join(politics_blocks)
    + "\n━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

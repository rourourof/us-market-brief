import os
import sys
import requests
from datetime import datetime, timedelta

# =====================
# 環境変数
# =====================
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

if not WEBHOOK_URL or not NEWS_API_KEY:
    print("ERROR: Environment variables not set")
    sys.exit(1)

# =====================
# JST時刻
# =====================
now_jst = datetime.utcnow() + timedelta(hours=9)

# =====================
# ニュース取得（前日分）
# =====================
def fetch_market_news():
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "US stock market OR Federal Reserve OR inflation OR interest rate",
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY,
    }

    r = requests.get(url, params=params)
    data = r.json()

    news = []
    for a in data.get("articles", []):
        title = a.get("title", "")
        source = a.get("source", {}).get("name", "")
        news.append(f"・{title}（{source}）")

    return news

news_list = fetch_market_news()

# =====================
# ① 前日のニュース → 株価影響
# =====================
if news_list:
    section_1 = (
        "【材料（前日のニュース）】\n"
        + "\n".join(news_list)
        + "\n\n【市場の解釈】\n"
        "・金利・インフレ関連のヘッドラインに市場は敏感\n"
        "・FRBのスタンス次第でハイテク株が動きやすい\n\n"
        "【株価への影響】\n"
        "・指数は方向感を探る展開\n"
        "・NASDAQは金利観測に反応しやすい一日"
    )
else:
    section_1 = (
        "【材料】\n"
        "前日は市場全体を大きく動かすニュースは確認されなかった。\n\n"
        "【市場の解釈】\n"
        "・材料難のため様子見姿勢が優勢\n\n"
        "【株価への影響】\n"
        "・指数は小動きにとどまった"
    )

# =====================
# メッセージ作成
# =====================
message = (
    "━━━━━━━━━━━━━━━━━━\n"
    "【米国株式市場ブリーフ】\n"
    "① 前日のニュースと株価への影響\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    f"{section_1}\n\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
payload = {"content": message}
res = requests.post(WEBHOOK_URL, json=payload)

print("STATUS:", res.status_code)

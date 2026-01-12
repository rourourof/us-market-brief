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
# 時刻判定（JST）
# =====================
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)
hour = now_jst.hour

MODE = "SCENARIO" if hour >= 17 else "REVIEW"

# =====================
# ニュース取得
# =====================
def fetch_news(query):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": 5,
        "apiKey": NEWS_API_KEY,
    }
    res = requests.get(url, params=params).json()
    return res.get("articles", [])

translator = GoogleTranslator(source="en", target="ja")

# =====================
# ニュース処理
# =====================
def build_news_section():
    articles = fetch_news(
        "US stock market semiconductor NVDA AMD Federal Reserve politics"
    )

    blocks = []

    for a in articles:
        title = translator.translate(a.get("title", ""))
        desc = translator.translate(a.get("description", ""))

        published = a.get("publishedAt")
        if published:
            dt = datetime.fromisoformat(published.replace("Z", "")) + timedelta(hours=9)
            date_str = dt.strftime("%Y/%m/%d %H:%M JST")
        else:
            date_str = "日時不明"

        if MODE == "SCENARIO":
            block = (
                f"・【{date_str}】{title}\n"
                f"{desc}\n"
                "▶ 市場では金利・ハイテク株への影響が意識される可能性\n"
            )
        else:
            block = (
                f"★【{date_str}】{title}\n"
                f"{desc}\n"
                "▶ 出来高と価格帯の反応を踏まえ、影響度を判定\n"
            )

        blocks.append(block)

    return "\n".join(blocks)

# =====================
# テクニカル分析（文章）
# =====================
def technical_section():
    if MODE == "SCENARIO":
        return (
            "【テクニカル状況】\n"
            "・NASDAQは20EMA上で推移\n"
            "・高値圏での持ち合いが継続\n"
            "・出来高は低下傾向で材料待ち\n\n"
            "【半導体】\n"
            "・SOX指数はNASDAQより相対的に強い\n"
            "・NVDAは押し目形成、AMDも下値は限定的\n\n"
            "【本日のシナリオ】\n"
            "・材料が意識され出来高増 → 上方向ブレイク\n"
            "・反応薄 → 高値圏での調整継続\n"
        )
    else:
        return (
            "【実際の値動き】\n"
            "・NASDAQは寄り付き後の値動きが焦点\n"
            "・出来高を伴うブレイクがあったかを確認\n\n"
            "【半導体の反応】\n"
            "・NVDAが指数より強ければ材料集中と判断\n"
            "・SOXが失速した場合は調整局面と評価\n\n"
            "【検証】\n"
            "・ニュースが効いたか／織り込み済みだったかを判定\n"
        )

# =====================
# メッセージ構築
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

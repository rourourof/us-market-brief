import os
import sys
import requests
from datetime import datetime, timedelta

# =========================
# 基本設定
# =========================
WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
NEWS_API_KEY = os.environ.get("NEWS_API_KEY")

if not WEBHOOK_URL:
    print("ERROR: DISCORD_WEBHOOK_URL not set")
    sys.exit(1)

# =========================
# JST 時刻・曜日判定
# =========================
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)

# 土曜は配信しない
if now_jst.weekday() == 5:
    print("Saturday (JST). Skip sending.")
    sys.exit(0)

hour = now_jst.hour  # 朝夕判定

# =========================
# ニュース取得関数
# =========================
def fetch_news(query, page_size=5):
    if not NEWS_API_KEY:
        return []

    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }

    r = requests.get(url, params=params)
    data = r.json()

    articles = []
    for a in data.get("articles", []):
        title = a.get("title", "")
        source = a.get("source", {}).get("name", "")
        articles.append(f"・{title}（{source}）")

    return articles

# =========================
# ① 前日のニュース → 株価影響
# =========================
market_news = fetch_news(
    "US stock market OR Federal Reserve OR inflation OR interest rate"
)

if market_news:
    previous_impact = (
        "【材料（前日のニュース）】\n"
        + "\n".join(market_news)
        + "\n\n【市場の解釈】\n"
        "・金融政策や金利見通しが意識されやすい状況\n"
        "・ハイテク株は金利動向に敏感な反応\n\n"
        "【株価の反応】\n"
        "・NASDAQは方向感を探る展開\n"
        "・半導体株は銘柄ごとに強弱が分かれた"
    )
else:
    previous_impact = "前日は市場全体を大きく動かすニュースは限定的だった。"

# =========================
# ② 半導体セクター（メイン）
# =========================
semiconductor_news = fetch_news(
    "semiconductor OR NVIDIA OR AMD OR Intel OR chip"
)

semiconductor = (
    "AI・データセンター需要を背景に半導体は引き続き市場の中心。\n\n"
    + ("\n".join(semiconductor_news) if semiconductor_news else "目立った半導体ニュースなし。")
    + "\n\n"
    "【セクター評価】\n"
    "・中長期では成長期待が維持\n"
    "・短期的には金利・指数動向に左右されやすい"
)

# =========================
# ③ 米国政治・政治家発言
# =========================
political_news = fetch_news(
    "US politics OR White House OR Congress OR Biden OR Trump"
)

politics = (
    "【注目された政治・政策動向】\n"
    + ("\n".join(political_news) if political_news else "市場に影響する政治ニュースは限定的。")
    + "\n\n"
    "【市場への影響】\n"
    "・政策不透明感は株価の上値を抑制\n"
    "・半導体政策は中長期では追い風との見方"
)

# =========================
# ④ 当日の株価変動振り返り
# =========================
today_market = (
    "【指数の動き】\n"
    "・S&P500 / NASDAQ / ダウの推移\n\n"
    "【値動きの特徴】\n"
    "・前日材料の消化が中心\n"
    "・半導体株が指数に与えた影響を確認"
)

# =========================
# 朝夕でヘッダ切替
# =========================
if hour < 12:
    header = "【米国株式市場モーニングブリーフ】"
    focus = "本日は前日のニュースと市場心理を中心に整理。"
else:
    header = "【米国株式市場イブニングブリーフ】"
    focus = "本日は実際の値動きを振り返る。"

# =========================
# メッセージ組み立て
# =========================
message = (
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"{header}\n"
    "（半導体・政治・市場総合）\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    f"{focus}\n\n"
    "■ ① 前日のニュースと株価への影響\n"
    f"{previous_impact}\n\n"
    "■ ② 半導体セクター動向（メイン）\n"
    f"{semiconductor}\n\n"
    "■ ③ 米国政治・政治家の発言\n"
    f"{politics}\n\n"
    "■ ④ 当日の株価変動の振り返り\n"
    f"{today_market}\n\n"
    "━━━━━━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻（JST）：{now_jst.strftime('%Y-%m-%d %H:%M')}\n"
    "※ 自動配信 / 投資助言ではありません"
)

# =========================
# Discord送信
# =========================
payload = {"content": message}
response = requests.post(WEBHOOK_URL, json=payload)

print("STATUS:", response.status_code)

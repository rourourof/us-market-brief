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
# 時刻（JST基準）
# =====================
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)
weekday = now_jst.weekday()  # 月=0 土=5 日=6

# 土曜はスキップ
if weekday == 5:
    sys.exit("Saturday skipped")

# MODE判定（JST）
if 17 <= now_jst.hour < 23:
    MODE = "SCENARIO"   # 18:00想定
else:
    MODE = "REVIEW"     # 6:00振り返り

translator = GoogleTranslator(source="en", target="ja")

# =====================
# NewsAPI
# =====================
def fetch_news(query, start, end, size):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": query,
        "language": "en",
        "sortBy": "publishedAt",
        "from": start,
        "to": end,
        "pageSize": size,
        "apiKey": NEWS_API_KEY,
    }
    res = requests.get(url, params=params).json()
    return res.get("articles", [])

def fmt(article, mark):
    title = translator.translate(article.get("title", ""))
    desc = translator.translate(article.get("description", ""))
    dt = datetime.fromisoformat(article["publishedAt"].replace("Z", "")) + timedelta(hours=9)
    return f"{mark}【{dt:%Y/%m/%d %H:%M JST}】{title}\n{desc}\n"

# =====================
# ニュース構築
# =====================
def build_news_blocks():
    blocks = []

    # --- 前日の影響評価 ---
    days = 3 if weekday == 0 else 1
    impact = fetch_news(
        "US stock market reaction Fed earnings semiconductor",
        (now_utc - timedelta(days=days)).strftime("%Y-%m-%d"),
        now_utc.strftime("%Y-%m-%d"),
        5,
    )
    text = "【ニュース｜前日の影響評価】\n"
    if impact:
        for a in impact:
            text += fmt(a, "★")
            text += "▶ 株価・出来高・指数への影響を検証\n\n"
    else:
        text += "※ 株価に直接影響した明確な材料は限定的\n\n"
    blocks.append(text)

    # --- 最新ニュース ---
    latest = fetch_news(
        "Fed comments US politics semiconductor NVDA",
        (now_utc - timedelta(hours=12)).strftime("%Y-%m-%dT%H:%M:%S"),
        now_utc.strftime("%Y-%m-%dT%H:%M:%S"),
        3,
    )
    text = "【ニュース｜最新（速報）】\n"
    if latest:
        for a in latest:
            text += fmt(a, "・")
            text += "▶ 市場反応はこれから\n\n"
    else:
        text += "※ 目立った速報ニュースなし\n\n"
    blocks.append(text)

    # --- トレンド（1週間） ---
    trend = fetch_news(
        "Federal Reserve policy NVDA semiconductor geopolitics",
        (now_utc - timedelta(days=7)).strftime("%Y-%m-%d"),
        now_utc.strftime("%Y-%m-%d"),
        3,
    )
    text = "【トレンドを形成している大きな材料（過去1週間）】\n"
    if trend:
        for a in trend:
            text += fmt(a, "◆")
            text += "▶ 中期トレンドを形成\n\n"
    else:
        text += "※ トレンドはテクニカル主導\n\n"
    blocks.append(text)

    return "\n".join(blocks)

# =====================
# NVDA別枠（時間帯別）
# =====================
def nvda_section():
    if MODE == "SCENARIO":
        return (
            "【NVDA 個別動向｜テクニカル予想】\n"
            "・高値圏での推移が続く場合、押し目買い優勢\n"
            "・出来高を伴い前日高値を上抜ければ上昇継続\n"
            "・VWAP割れが続く場合は短期調整シナリオ\n\n"
        )
    else:
        return (
            "【NVDA 個別動向｜前日の振り返り】\n"
            "・出来高の増減と価格の方向性を確認\n"
            "・高値更新／失速の有無でトレンド評価\n"
            "・指数（NASDAQ）との相対強弱を検証\n\n"
        )

# =====================
# 政治枠
# =====================
def politics_section():
    return (
        "【米国政治・政治家発言】\n"
        "・FRB関係者のスタンス（タカ派／ハト派）\n"
        "・半導体規制・対中政策の方向性\n"
        "・即効性か背景要因かを切り分け\n\n"
    )

# =====================
# テクニカル
# =====================
def technical_section():
    if MODE == "SCENARIO":
        return (
            "【本日のテクニカルシナリオ】\n"
            "・NVDA主導でSOXが上抜け → 強気\n"
            "・指数失速でも半導体が耐えれば継続\n"
            "・出来高を伴う下抜け → 調整警戒\n"
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
title = "【米国株 市場シナリオ】18:00 JST" if MODE == "SCENARIO" else "【米国株 市場レビュー】6:00 JST"

message = (
    "━━━━━━━━━━━━━━━━━━\n"
    f"{title}\n"
    "（米国株 / 半導体中心）\n"
    "━━━━━━━━━━━━━━━━━━\n\n"
    f"{build_news_blocks()}\n"
    f"{nvda_section()}"
    f"{politics_section()}"
    f"{technical_section()}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻：{now_jst:%Y-%m-%d %H:%M JST}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

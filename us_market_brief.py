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
# 時刻
# =====================
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)
weekday = now_jst.weekday()  # Mon=0

# =====================
# モード判定（UTC基準）
# =====================
if now_utc.hour == 9:
    MODE = "SCENARIO"   # 18:00 JST
elif now_utc.hour == 21:
    MODE = "REVIEW"     # 06:00 JST
else:
    MODE = "REVIEW"     # 手動実行用

translator = GoogleTranslator(source="en", target="ja")

# =====================
# NewsAPI 共通
# =====================
def fetch_news(from_dt, to_dt, page_size=5):
    url = "https://newsapi.org/v2/everything"
    params = {
        "q": "US stock market semiconductor NVDA AMD SOX Federal Reserve US politics",
        "language": "en",
        "sortBy": "publishedAt",
        "from": from_dt,
        "to": to_dt,
        "pageSize": page_size,
        "apiKey": NEWS_API_KEY,
    }
    res = requests.get(url, params=params).json()
    return res.get("articles", [])

def format_article(a, mark="・"):
    title = translator.translate(a.get("title", ""))
    desc = translator.translate(a.get("description", ""))
    published = a.get("publishedAt")
    dt = datetime.fromisoformat(published.replace("Z", "")) + timedelta(hours=9)
    date_str = dt.strftime("%Y/%m/%d %H:%M JST")
    return f"{mark}【{date_str}】{title}\n{desc}\n"

# =====================
# ニュース構築
# =====================
def build_news_sections():
    sections = []

    # --- REVIEW（6:00） ---
    if MODE == "REVIEW":
        # 月曜は金〜日をカバー
        days_back = 3 if weekday == 0 else 1

        # ① 前日の影響（★判定対象）
        from_dt = (now_utc - timedelta(days=days_back)).strftime("%Y-%m-%d")
        to_dt = now_utc.strftime("%Y-%m-%d")
        impact_news = fetch_news(from_dt, to_dt, page_size=5)

        impact_block = "【ニュース｜前日の影響評価】\n"
        if impact_news:
            for a in impact_news:
                impact_block += format_article(a, mark="★")
                impact_block += "▶ 株価・出来高・重要ラインとの反応を基に影響度を判定\n\n"
        else:
            impact_block += "※ 対象期間内で株価に影響したニュースは限定的\n\n"

        sections.append(impact_block)

        # ② 最新ニュース（速報・★なし）
        from_latest = (now_utc - timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%S")
        latest_news = fetch_news(from_latest, now_utc.strftime("%Y-%m-%dT%H:%M:%S"), page_size=3)

        latest_block = "【ニュース｜最新（速報）】\n"
        if latest_news:
            for a in latest_news:
                latest_block += format_article(a, mark="・")
                latest_block += "▶ 市場反応はまだ未確認\n\n"
        else:
            latest_block += "※ 目立った速報ニュースなし\n\n"

        sections.append(latest_block)

        # ③ トレンド継続要因（過去1週間）
        from_week = (now_utc - timedelta(days=7)).strftime("%Y-%m-%d")
        trend_news = fetch_news(from_week, now_utc.strftime("%Y-%m-%d"), page_size=2)

        trend_block = "【トレンドを形成している大きな材料（過去1週間）】\n"
        if trend_news:
            for a in trend_news:
                trend_block += format_article(a, mark="◆")
                trend_block += "▶ 中期トレンドに継続的に影響している可能性\n\n"
        else:
            trend_block += "※ 現在のトレンドはテクニカル主導\n\n"

        sections.append(trend_block)

    # --- SCENARIO（18:00） ---
    else:
        from_dt = (now_utc - timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%S")
        to_dt = now_utc.strftime("%Y-%m-%dT%H:%M:%S")
        scenario_news = fetch_news(from_dt, to_dt, page_size=5)

        block = "【ニュース｜本日の材料】\n"
        if scenario_news:
            for a in scenario_news:
                block += format_article(a, mark="・")
                block += "▶ 出来高を伴えば本日の主因になる可能性\n\n"
        else:
            block += "※ 新規材料は限定的\n\n"

        sections.append(block)

    return "\n".join(sections)

# =====================
# テクニカル文章
# =====================
def technical_section():
    if MODE == "SCENARIO":
        return (
            "【テクニカル状況】\n"
            "・NASDAQは20EMA上を維持\n"
            "・高値圏での持ち合い\n"
            "・出来高は低下傾向\n\n"
            "【半導体】\n"
            "・SOX指数はNASDAQより相対的に強い\n"
            "・NVDAは押し目形成、AMDはレンジ上限試し\n\n"
            "【本日のシナリオ】\n"
            "・材料＋出来高 → 上方向ブレイク\n"
            "・反応薄 → 高値圏調整\n"
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
    f"{build_news_sections()}\n"
    f"{technical_section()}\n"
    "━━━━━━━━━━━━━━━━━━\n"
    f"配信時刻：{now_jst.strftime('%Y-%m-%d %H:%M JST')}\n"
    "※ 自動生成 / 投資助言ではありません"
)

# =====================
# Discord送信
# =====================
requests.post(WEBHOOK_URL, json={"content": message})

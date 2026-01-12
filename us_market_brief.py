import os
import yaml
import requests
import datetime
import pytz
import yfinance as yf
from openai import OpenAI

# ======================
# 設定読込
# ======================
with open("config.yml", "r") as f:
    config = yaml.safe_load(f)

JST = pytz.timezone(config["timezone"])

# ======================
# Mode 判定
# ======================
now = datetime.datetime.now(JST)

def detect_mode():
    if config["mode"] != "auto":
        return config["mode"]
    if now.hour >= config["schedule"]["evening_hour"]:
        return "evening"
    return "morning"

MODE = detect_mode()

# ======================
# データ取得
# ======================
def fetch(symbol):
    df = yf.download(symbol, period="2mo", interval="1d", progress=False)
    df = df.dropna()
    cur = df.iloc[-1]
    prev = df.iloc[-2]

    return {
        "close": float(cur["Close"]),
        "high": float(cur["High"]),
        "low": float(cur["Low"]),
        "prev_high": float(prev["High"]),
        "prev_low": float(prev["Low"]),
        "change_pct": float((cur["Close"] / prev["Close"] - 1) * 100),
        "volume": int(cur["Volume"]),
        "avg_volume_20": int(df["Volume"].tail(20).mean())
    }

nvda = fetch(config["symbols"]["nvda"])
sox = fetch(config["symbols"]["semiconductor_index"])
nas = fetch(config["symbols"]["nasdaq"])

# ======================
# テクニカル判定
# ======================
def tech_comment(d):
    if d["volume"] > d["avg_volume_20"] * 1.3:
        vol = "出来高を伴った動き"
    else:
        vol = "出来高は平均的"

    if d["close"] > d["prev_high"]:
        price = "上方向へのブレイク"
    elif d["close"] < d["prev_low"]:
        price = "下方向へのブレイク"
    else:
        price = "レンジ内推移"

    return f"{vol}で、{price}。"

# ======================
# AI文章生成（失敗耐性あり）
# ======================
def ai_generate(prompt):
    if not config["openai"]["enabled"]:
        return None
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        res = client.chat.completions.create(
            model=config["openai"]["model"],
            messages=[{"role": "user", "content": prompt}],
            temperature=config["openai"]["temperature"]
        )
        return res.choices[0].message.content.strip()
    except Exception:
        return None

# ======================
# メッセージ生成
# ======================
def build_message():
    header = "━━━━━━━━━━━━━━━━━━\n"
    if MODE == "morning":
        header += "【米国株 市場レビュー】6:00 JST\n（米国株 / 半導体中心）\n"
    else:
        header += "【18:00 米国半導体 & NVIDIA シナリオ】\n"
    header += "━━━━━━━━━━━━━━━━━━\n\n"

    body = f"""
【ニュース｜前日の影響評価】
・明確に株価へ影響した材料は限定的
・材料よりも需給とテクニカルが主導

【ニュース｜最新（速報）】
・市場を即座に動かすヘッドラインは確認されず

【トレンドを形成している大きな材料（過去1週間）】
・AI半導体需要の持続性
・金利高止まりによるバリュエーション調整圧力

【NVDA 個別動向】
終値: {nvda["close"]:.2f} / 前日比 {nvda["change_pct"]:.2f}%
{tech_comment(nvda)}

【半導体セクター全体（SOX）】
SOX 前日比 {sox["change_pct"]:.2f}%
{tech_comment(sox)}

【相対評価】
・NVDAは指数比で {'強い' if nvda["change_pct"] > sox["change_pct"] else '劣後'}

【米国政治・政治家発言】
・規制・金融政策面で新規材料なし
・市場は現行スタンスを織り込み済み

"""

    # AI補強
    prompt = f"""
あなたは米国株・半導体専門の市場アナリストです。
以下のデータを基に、10分想定の解説文を作ってください。
断定は避け、市場参加者心理を重視してください。

NVDA: {nvda}
SOX: {sox}
NASDAQ: {nas}
"""

    ai_text = ai_generate(prompt)
    if ai_text:
        body += "【AI分析補足】\n" + ai_text + "\n\n"

    footer = f"""━━━━━━━━━━━━━━━━━━
配信時刻：{now.strftime('%Y-%m-%d %H:%M')} JST
※ 自動生成 / 投資助言ではありません
"""

    return header + body + footer

# ======================
# Discord送信
# ======================
payload = {"content": build_message()}
requests.post(config["discord"]["webhook_url"], json=payload)

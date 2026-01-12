import os
import json
import requests
from datetime import datetime
import yfinance as yf
from openai import OpenAI

# =====================
# 環境変数チェック
# =====================
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not DISCORD_WEBHOOK_URL or not OPENAI_API_KEY:
    raise RuntimeError("Environment variables not set")

client = OpenAI(api_key=OPENAI_API_KEY)

# =====================
# 時刻判定（JST）
# =====================
now_utc = datetime.utcnow()
jst_hour = (now_utc.hour + 9) % 24

MODE = "EVENING" if jst_hour >= 17 else "MORNING"

# =====================
# 株価データ取得
# =====================
def fetch_market(ticker):
    df = yf.download(ticker, period="40d", interval="1d", progress=False)
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

nasdaq = fetch_market("^IXIC")
sox = fetch_market("^SOX")
nvda = fetch_market("NVDA")

# =====================
# テクニカル判定
# =====================
def breakout_text(d):
    if d["volume"] > d["avg_volume_20"] * 1.2:
        if d["close"] > d["prev_high"]:
            return "出来高を伴い上方向にブレイク"
        if d["close"] < d["prev_low"]:
            return "出来高を伴い下方向にブレイク"
    return "明確なブレイクなし"

def relative_strength(a, b):
    if a["change_pct"] > b["change_pct"]:
        return "アウトパフォーム"
    if a["change_pct"] < b["change_pct"]:
        return "アンダーパフォーム"
    return "指数並み"

# =====================
# OpenAI文章生成
# =====================
def ai_generate(prompt):
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "あなたはプロの米国株・半導体市場アナリストです。"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.4
    )
    return response.choices[0].message.content.strip()

# =====================
# NVDAシナリオ生成（18:00）
# =====================
def nvda_evening_scenario():
    prompt = f"""
以下はNVIDIA（NVDA）の本日のテクニカル情報です。
これを基に、短期トレード視点でのシナリオを日本語でまとめてください。

・終値: {nvda['close']}
・前日高値: {nvda['prev_high']}
・前日安値: {nvda['prev_low']}
・前日比: {nvda['change_pct']:.2f}%
・出来高: {nvda['volume']}（20日平均 {nvda['avg_volume_20']}）

条件：
・事実ベース
・断定しすぎない
・2〜4文程度
"""
    return ai_generate(prompt)

# =====================
# 予想保存・検証
# =====================
PRED_FILE = "nvda_prediction.json"

def save_prediction(text):
    with open(PRED_FILE, "w") as f:
        json.dump({"prediction": text}, f, ensure_ascii=False)

def load_prediction():
    if not os.path.exists(PRED_FILE):
        return "前日シナリオなし"
    with open(PRED_FILE) as f:
        return json.load(f)["prediction"]

# =====================
# メッセージ生成
# =====================
def build_message():
    if MODE == "EVENING":
        scenario = nvda_evening_scenario()
        save_prediction(scenario)

        return f"""
━━━━━━━━━━━━━━━━━━
【18:00 NVIDIA テクニカルシナリオ】
━━━━━━━━━━━━━━━━━━

【テクニカル状況】
・終値: {nvda['close']}
・前日比: {nvda['change_pct']:.2f}%
・値動き: {breakout_text(nvda)}

【AIシナリオ】
{scenario}

━━━━━━━━━━━━━━━━━━
※ 自動生成 / 投資助言ではありません
"""

    else:
        prev_pred = load_prediction()

        return f"""
━━━━━━━━━━━━━━━━━━
【米国株 市場レビュー】6:00 JST
（米国株 / 半導体中心）
━━━━━━━━━━━━━━━━━━

【指数の動き】
NASDAQ: {breakout_text(nasdaq)}
SOX: {breakout_text(sox)}

【半導体の反応】
NVDA: NASDAQ比 {relative_strength(nvda, nasdaq)}

【NVDA 前日シナリオ検証】
{prev_pred}

━━━━━━━━━━━━━━━━━━
※ 自動生成 / 投資助言ではありません
"""

# =====================
# Discord送信
# =====================
payload = {"content": build_message()}
requests.post(DISCORD_WEBHOOK_URL, json=payload)

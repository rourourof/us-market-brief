import os
import json
import requests
from datetime import datetime
import yfinance as yf
from openai import OpenAI

# =====================
# 環境変数
# =====================
DISCORD_WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

if not DISCORD_WEBHOOK_URL:
    raise RuntimeError("DISCORD_WEBHOOK_URL not set")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================
# 時刻判定（JST）
# =====================
now_utc = datetime.utcnow()
jst_hour = (now_utc.hour + 9) % 24
weekday = now_utc.weekday()  # Mon=0

if weekday >= 5:
    exit()  # 土日除外

MODE = "EVENING" if jst_hour >= 17 else "MORNING"

# =====================
# 株価取得（Warning回避）
# =====================
def fetch_market(ticker):
    df = yf.download(ticker, period="40d", interval="1d", progress=False).dropna()

    cur = df.iloc[-1]
    prev = df.iloc[-2]

    return {
        "close": float(cur["Close"].item()),
        "high": float(cur["High"].item()),
        "low": float(cur["Low"].item()),
        "prev_high": float(prev["High"].item()),
        "prev_low": float(prev["Low"].item()),
        "change_pct": float(((cur["Close"] / prev["Close"]) - 1).item() * 100),
        "volume": int(cur["Volume"].item()),
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
# AI生成（Quota切れ耐性）
# =====================
def ai_generate(prompt):
    if not client:
        raise RuntimeError("OpenAI client not available")

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
# NVDAシナリオ（AI + fallback）
# =====================
def nvda_scenario():
    base = (
        f"終値 {nvda['close']:.2f} / 前日比 {nvda['change_pct']:.2f}%。\n"
        f"{breakout_text(nvda)}。"
    )

    prompt = f"""
以下はNVIDIA（NVDA）の本日のテクニカル情報です。
短期視点のシナリオを日本語で2〜4文で。

{base}
"""

    try:
        return ai_generate(prompt)
    except Exception:
        # フォールバック（条件維持）
        if nvda["close"] > nvda["prev_high"]:
            return base + " 上方向へのトレンド継続が意識されやすい。"
        if nvda["close"] < nvda["prev_low"]:
            return base + " 調整色が強く、戻り売り警戒。"
        return base + " 方向感待ちの調整局面。"

# =====================
# 予想保存・検証
# =====================
PRED_FILE = "nvda_prediction.json"

def save_pred(text):
    with open(PRED_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": text}, f, ensure_ascii=False)

def load_pred():
    if not os.path.exists(PRED_FILE):
        return "前日シナリオなし"
    with open(PRED_FILE, encoding="utf-8") as f:
        return json.load(f)["text"]

# =====================
# メッセージ生成
# =====================
def build_message():
    if MODE == "EVENING":
        scenario = nvda_scenario()
        save_pred(scenario)

        return f"""
━━━━━━━━━━━━━━━━━━
【18:00 NVIDIA テクニカルシナリオ】
━━━━━━━━━━━━━━━━━━

【NVDA】
終値: {nvda['close']:.2f}
前日比: {nvda['change_pct']:.2f}%
値動き: {breakout_text(nvda)}

【シナリオ】
{scenario}

※ 自動生成 / 投資助言ではありません
"""

    else:
        return f"""
━━━━━━━━━━━━━━━━━━
【米国株 市場レビュー】6:00 JST
（米国株 / 半導体中心）
━━━━━━━━━━━━━━━━━━

【指数】
NASDAQ: {breakout_text(nasdaq)}
SOX: {breakout_text(sox)}

【半導体】
NVDA: NASDAQ比 {relative_strength(nvda, nasdaq)}

【前日18:00 NVDAシナリオ検証】
{load_pred()}

※ 自動生成 / 投資助言ではありません
"""

# =====================
# Discord送信
# =====================
requests.post(
    DISCORD_WEBHOOK_URL,
    json={"content": build_message()},
    timeout=10
)

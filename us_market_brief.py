import yfinance as yf
import pandas as pd
from datetime import datetime
import json
import os

# =====================
# 時刻・モード判定
# =====================
now = datetime.utcnow()
JST_HOUR = (now.hour + 9) % 24

if JST_HOUR >= 17:
    MODE = "EVENING"   # 18:00 シナリオ
else:
    MODE = "MORNING"   # 6:00 レビュー

# =====================
# データ取得
# =====================
def fetch(ticker):
    df = yf.download(ticker, period="40d", interval="1d", progress=False)
    df = df.dropna()
    cur = df.iloc[-1]
    prev = df.iloc[-2]

    return {
        "close": float(cur["Close"]),
        "open": float(cur["Open"]),
        "high": float(cur["High"]),
        "low": float(cur["Low"]),
        "ph": float(prev["High"]),
        "pl": float(prev["Low"]),
        "chg": float((cur["Close"] / prev["Close"] - 1) * 100),
        "vol": int(cur["Volume"]),
        "vol20": int(df["Volume"].tail(20).mean())
    }

nas = fetch("^IXIC")
sox = fetch("^SOX")
nvda = fetch("NVDA")

# =====================
# テクニカル判定
# =====================
def breakout(d):
    if d["vol"] > d["vol20"] * 1.2:
        if d["close"] > d["ph"]:
            return "上方向ブレイク（出来高伴う）"
        if d["close"] < d["pl"]:
            return "下方向ブレイク（出来高伴う）"
    return "ブレイクなし"

def rel(a, b):
    if a["chg"] > b["chg"]:
        return "アウトパフォーム"
    if a["chg"] < b["chg"]:
        return "アンダーパフォーム"
    return "指数並み"

# =====================
# NVIDIA予想保存 / 検証
# =====================
PRED_FILE = "nvda_prediction.json"

def save_prediction(text):
    with open(PRED_FILE, "w") as f:
        json.dump({
            "date": now.strftime("%Y-%m-%d"),
            "text": text
        }, f)

def validate_prediction():
    if not os.path.exists(PRED_FILE):
        return "前日予想なし"

    with open(PRED_FILE) as f:
        pred = json.load(f)

    if nvda["close"] > nvda["ph"]:
        result = "上"
    elif nvda["close"] < nvda["pl"]:
        result = "下"
    else:
        result = "レンジ"

    return f"結果：{result} ／ 前日予想：{pred['text']}"

# =====================
# 出力
# =====================
print("━━━━━━━━━━━━━━━━━━")
print("【米国株 市場レビュー】6:00 JST")
print("（米国株 / 半導体中心）")
print("━━━━━━━━━━━━━━━━━━")

if MODE == "MORNING":
    print("\n【ニュース｜前日の影響評価】")
    print("※ 株価に直接影響した明確な材料は限定的")

    print("\n【ニュース｜最新（速報）】")
    print("※ 目立った速報ニュースなし")

    print("\n【トレンドを形成している大きな材料（過去1週間）】")
    print("※ テクニカル主導")

    print("\n【NVDA 個別動向】")
    print(f"相対強弱：{rel(nvda, nas)}")

    print("\n【米国政治・政治家発言】")
    print("※ 市場を動かす発言なし")

    print("\n【実際の値動き】")
    print(f"NASDAQ：{breakout(nas)}")
    print(f"SOX：{breakout(sox)}")

    print("\n【半導体の反応】")
    print(f"NVDA：{rel(nvda, nas)}")

    print("\n【検証】")
    print(validate_prediction())

else:
    outlook = "レンジ想定"
    if nvda["close"] > nvda["ph"]:
        outlook = "上方向警戒"
    elif nvda["close"] < nvda["pl"]:
        outlook = "下方向警戒"

    save_prediction(outlook)

    print("\n【18:00 NVIDIA テクニカルシナリオ】")
    print(f"前日高値：{nvda['ph']}")
    print(f"前日安値：{nvda['pl']}")
    print(f"想定：{outlook}")

print("\n━━━━━━━━━━━━━━━━━━")
print(f"配信時刻：{now.strftime('%Y-%m-%d %H:%M')} JST")
print("※ 自動生成 / 投資助言ではありません")

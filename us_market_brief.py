# us_market_brief.py
import os, requests, pytz, yfinance as yf, pandas as pd
from datetime import datetime, timedelta
import openai
import matplotlib.pyplot as plt

# =====================
# ENV
# =====================
DISCORD_WEBHOOK_URL = os.getenv("DISCORD_WEBHOOK_URL")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
if not all([DISCORD_WEBHOOK_URL, OPENAI_API_KEY, NEWS_API_KEY]):
    raise RuntimeError("Environment variables not set")

openai.api_key = OPENAI_API_KEY
JST = pytz.timezone("Asia/Tokyo")
now = datetime.now(JST)

# =====================
# MODE（完全分離）
# =====================
if now.hour == 18:
    mode = "scenario"
elif now.hour == 6:
    mode = "review"
else:
    mode = "manual"

# =====================
# AI CALL
# =====================
def ai_call(system, user, temp=0.3):
    r = openai.ChatCompletion.create(
        model="gpt-4o-mini",
        messages=[{"role":"system","content":system},{"role":"user","content":user}],
        temperature=temp
    )
    return r.choices[0].message.content.strip()

NEWS_SYS = "ニュースを★△×で影響度評価し、日本語で内容中心に要約。"
TECH_SYS = "出来高・ブレイク・調整・相対強弱でテクニカル解釈。"
NVDA_SCN_SYS = "NVDAの翌セッション・テクニカルシナリオ（上/下/横）。"
VERIFY_SYS = "18:00シナリオと実際の値動きを比較し理由を整理。"

# =====================
# MARKET DATA
# =====================
def get_data(t):
    df = yf.download(t, period="2mo", interval="1d", progress=False).dropna()
    cur, prev = df.iloc[-1], df.iloc[-2]
    return {
        "close": round(cur["Close"],2),
        "chg": round((cur["Close"]-prev["Close"])/prev["Close"]*100,2),
        "vol": int(cur["Volume"]),
        "vol20": int(df["Volume"].tail(20).mean()),
        "high": float(cur["High"]),
        "low": float(cur["Low"]),
        "ph": float(prev["High"]),
        "pl": float(prev["Low"]),
        "df": df
    }

def tech_flags(d):
    return {
        "vol_spike": d["vol"] > d["vol20"]*1.5,
        "break_up": d["high"] > d["ph"],
        "break_dn": d["low"] < d["pl"]
    }

def rel_strength(a,b):
    return "アウトパフォーム" if a["chg"]>b["chg"] else "アンダーパフォーム" if a["chg"]<b["chg"] else "指数並み"

# =====================
# NEWS
# =====================
def fetch_news(days):
    url="https://newsapi.org/v2/everything"
    params={
        "q":"(Nvidia OR NVDA OR semiconductor) OR (US politics OR Fed)",
        "from":(datetime.utcnow()-timedelta(days=days)).strftime("%Y-%m-%d"),
        "language":"en","pageSize":10,"apiKey":NEWS_API_KEY
    }
    return requests.get(url,params=params,timeout=20).json().get("articles",[])

def titles(arts):
    return "\n".join([f"- {a['title']} ({a['source']['name']})" for a in arts]) or "該当なし"

news_1d = titles(fetch_news(1))
news_7d = titles(fetch_news(7))

# =====================
# FETCH
# =====================
nas = get_data("^IXIC")
sox = get_data("^SOX")
nvda = get_data("NVDA")

nas_f, sox_f, nv_f = tech_flags(nas), tech_flags(sox), tech_flags(nvda)

nv_fact = f"""
終値 {nvda['close']}（{nvda['chg']}%）
出来高 {'増加' if nv_f['vol_spike'] else '平常'}
値動き {'高値ブレイク' if nv_f['break_up'] else 'レンジ/調整'}
相対強弱 {rel_strength(nvda,nas)}
"""

# =====================
# AI
# =====================
news_eval = ai_call(NEWS_SYS, news_1d)
trend_eval = ai_call(NEWS_SYS, news_7d)
market_eval = ai_call(TECH_SYS, f"NASDAQ:{nas}\nSOX:{sox}")

if mode=="scenario":
    nv_block = ai_call(NVDA_SCN_SYS, nv_fact)
    verify_block = "※ 翌朝6:00に検証"
else:
    nv_block = nv_fact
    verify_block = ai_call(VERIFY_SYS, nv_fact)

# =====================
# OPTIONAL: 可視化（NVDA）
# =====================
plt.figure()
nvda["df"]["Close"].tail(30).plot(title="NVDA Close (30D)")
img="nvda.png"
plt.savefig(img); plt.close()

# =====================
# JOURNAL（簡易保存）
# =====================
with open("journal.txt","a",encoding="utf-8") as f:
    f.write(f"{now.isoformat()} {mode} NVDA {nvda['chg']}%\n")

# =====================
# MESSAGE
# =====================
title = "【米国株 シナリオ】18:00 JST" if mode=="scenario" else "【米国株 市場レビュー】6:00 JST"
msg=f"""
━━━━━━━━━━━━━━━━━━
{title}
（米国株 / 半導体中心）
━━━━━━━━━━━━━━━━━━

【ニュース｜前日の影響評価】
{news_eval}

【ニュース｜最新（速報）】
{news_1d}

【トレンドを形成している材料（過去1週間）】
{trend_eval}

【NVDA 個別動向】
{nv_block}

【米国政治・政治家発言】
※ 半導体・金利への影響有無を精査

【実際の値動き（テクニカル）】
{market_eval}

【検証】
{verify_block}

━━━━━━━━━━━━━━━━━━
配信時刻：{now.strftime("%Y-%m-%d %H:%M")} JST
※ 自動生成 / 投資助言ではありません
"""

requests.post(DISCORD_WEBHOOK_URL, json={"content": msg})

import os
import requests
from datetime import datetime

# Discord Webhook
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

def send_discord(message: str):
    payload = {
        "content": message
    }
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    r.raise_for_status()

# ===== 市場ブリーフ本文 =====

today = datetime.utcnow().strftime("%Y-%m-%d")

message = f"""
📈 米国株 市場ブリーフ

【半導体セクター】
・NVDA / AMD / INTC の動向
・前日のニュースが株価に与えた影響

【米国政治】
・大統領・FRB・議会の発言
・マーケットへの影響

【市場振り返り】
・NASDAQ / S&P500
・当日の値動きまとめ
"""

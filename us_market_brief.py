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
📈 **米国株 市場ブリーフ（{today}）**

【半導体セクター】
・NVDA：前日のAI関連ニュースを受けた値動き
・AMD：競合比較と市場反応
・INTC：構造改革・政府支援の影響

【前日のニュース → 株価への影響】
・前日のマクロ／企業ニュースが
  当日のNASDAQ・SOX指数にどう反映されたか

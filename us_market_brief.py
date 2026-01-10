import os
import requests
from datetime import datetime

# ===== Discord Webhook =====
DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

def send_discord(message: str):
    payload = {"content": message}
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    r.raise_for_status()

# ===== 日付 =====
today = datetime.utcnow().strftime("%Y-%m-%d")

# ===== メッセージ本文（三重クォート不使用） =====
lines = [
    f"📈 米国株 市場ブリーフ（{today}）",
    "",
    "━━━━━━━━━━━━━━",
    "■ 半導体セクター",
    "━━━━━━━━━━━━━━",
    "・NVDA：AI・データセンター関連の材料と株価反応",
    "・AMD：競合比較と市場評価",
    "・INTC：構造改革・政府支援策の影響",
    "",
    "━━━━━━━━━━━━━━",
    "■ 前日のニュース → 株価への影響",
    "━━━━━━━━━━━━━━",
    "・前日に出た企業／マクロニュースが",
    "  当日のNASDAQ・SOX指数にどう反映されたか",
    "",
    "━━━━━━━━━━━━━━",
    "■ 当日の市場振り返り",
    "━━━━━━━━━━━━━━",
    "・NASDAQ / S&P500 の動き",
    "・

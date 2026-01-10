import os
import requests
from datetime import datetime

DISCORD_WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

def send_discord(message):
    payload = {"content": message}
    r = requests.post(DISCORD_WEBHOOK_URL, json=payload)
    r.raise_for_status()

today = datetime.utcnow().strftime("%Y-%m-%d")

lines = [
    f"US MARKET BRIEF ({today})",
    "",
    "SEMICONDUCTORS",
    "- NVDA : AI and data center related moves",
    "- AMD  : Competitive positioning",
    "- INTC : Restructuring and policy impact",
    "",
    "NEWS IMPACT",
    "- How yesterday's news affected today's prices",
    "",
    "MARKET REVIEW",
    "- NASDAQ and S&P500 movement",
    "- Intraday price action",
    "",
    "US POLITICS",
    "- President / Fed / Congress statements",
    "- Market implications",
    "",
    "This report is auto generated"
]

message = "\n".join(lines)

send_discord(message)

print("Discord notification sent successfully")

import os
import requests
from datetime import datetime, timezone, timedelta

WEBHOOK_URL = os.environ.get("DISCORD_WEBHOOK_URL")

if not WEBHOOK_URL:
    print("ERROR: Environment variables not set")
    exit(1)

JST = timezone(timedelta(hours=9))
today = datetime.now(JST).strftime("%Y-%m-%d")

def send_discord(message):
    payload = {"content": message}
    requests.post(WEBHOOK_URL, json=payload, timeout=10)

def main():
    message = f"""
📊 **米国市場レポート（{today}）**

【市場ニュース】
・米国の主要経済指標を受け、金利動向への警戒が続いている。
・インフレ鈍化期待が残る一方、FRB高金利長期化観測も根強い。

【ニュース要約（日本語）】
米経済指標は市場予想と概ね一致し、サプライズは限定的。
ただし直近の強い株価上昇を受け、材料出尽くしによる調整が意識されやすい。

【テクニカル分析】
・指数は20EMAの上で推移し、短期トレンドは上向き。
・前日は出来高を伴って高値圏をブレイク。
・2日前の好材料の影響が継続する一方、RSIはやや過熱気味。

【シナリオ】
上昇トレンドは維持されやすいが、高値圏では押し目や調整に注意。
出来高を伴った続伸があれば、次のレジスタンス試し。

【翌朝の答え合わせ視点】
・ブレイク後の出来高は維持されたか
・ニュースよりテクニカルが優先されたか
"""

    send_discord(message)

if __name__ == "__main__":
    main()

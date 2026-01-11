import os
import requests

print("DEBUG: script started")

WEBHOOK_URL = os.environ["DISCORD_WEBHOOK_URL"]

message = (
    "【米国市場デイリーブリーフ】\n\n"
    "■ 半導体セクター\n"
    "・NVIDIA / AMD / Intel の動向まとめ\n"
    "・前日のニュースが株価に与えた影響\n\n"
    "■ 米国政治\n"
    "・政権・議会・要人発言の要点\n"
    "・市場への影響ポイント\n\n"
    "※ テスト配信"
)

payload = {
    "content": message
}

response = requests.post(WEBHOOK_URL, json=payload)

print("STATUS:", response.status_code)
print("DEBUG: script finished")

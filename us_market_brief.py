import os

FROM_EMAIL = os.environ["GMAIL_ADDRESS"]
APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TO_EMAIL = os.environ["TO_EMAIL"]
print("DEBUG: script started")

# （ここにニュース取得や本文作成のコードがある前提）

print("DEBUG: about to send email")
print("FROM =", FROM_EMAIL)
print("TO =", TO_EMAIL)

# メール送信処理（sendmail / send_message の直後）
print("DEBUG: email send function finished")

print("DEBUG: script reached end")

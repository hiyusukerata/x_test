import streamlit as st
import requests
from datetime import datetime
import time

# --- セットアップ ---
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANpT1wEAAAAAdsiy7QKu48ZE2ECpAeiHF3jXX%2FQ%3Dh6E0IKyk970kbBOs4dTgOGkL8pyunmPHn5shLhVx671EHydlMy"
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

@st.cache_data(ttl=3600)
def get_user_info(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics"
    response = requests.get(url, headers=HEADERS)
    
    if response.status_code == 429:
        reset_unix = int(response.headers.get("x-rate-limit-reset", time.time() + 900))
        reset_time = datetime.fromtimestamp(reset_unix).strftime('%Y-%m-%d %H:%M:%S')
        return {"error": "Rate limit exceeded", "reset_time": reset_time}

    elif response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}
    
    return response.json()

# --- UI ---
st.title("X（Twitter）フォロワー追跡")

username = st.text_input("X（Twitter）ユーザー名（@なし）を入力", value="GoodAppsbyGMO")
if st.button("データを取得") and username:
    data = get_user_info(username)

    if "error" in data:
        st.error(f"エラー: {data['error']}")
        if "reset_time" in data:
            st.warning(f"リクエスト制限は {data['reset_time']} にリセットされます")
    elif "data" in data:
        metrics = data["data"]["public_metrics"]
        st.metric("フォロワー数", f"{metrics['followers_count']:,}")
        st.metric("フォロー数", f"{metrics['following_count']:,}")
        st.metric("ツイート数", f"{metrics['tweet_count']:,}")

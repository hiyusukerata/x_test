import streamlit as st
import requests

# --- 設定 ---
BEARER_TOKEN = "YOUR_BEARER_TOKEN_HERE"  # Secretsにするのがベスト
BASE_URL = "https://api.twitter.com/2/users/by/username/"

# --- ヘッダー定義 ---
HEADERS = {
    "Authorization": f"Bearer {BEARER_TOKEN}"
}

# --- ユーザー情報取得関数 ---
def get_user_info(username):
    url = f"{BASE_URL}{username}?user.fields=public_metrics"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API error: {response.status_code}"}

# --- Streamlit UI ---
st.title("X（旧Twitter）情報取得アプリ")

tabs = st.tabs(["ユーザー情報", "将来の機能1", "将来の機能2"])

with tabs[0]:
    st.subheader("アカウント情報を取得")
    username = st.text_input("XのアカウントID（@なし）を入力")
    if st.button("取得"):
        if username:
            data = get_user_info(username)
            if "error" in data:
                st.error(data["error"])
            elif "data" in data:
                metrics = data["data"]["public_metrics"]
                st.write(f"👤 ユーザー名: {data['data']['username']}")
                st.write(f"🧍‍♂️ フォロー数: {metrics['following_count']}")
                st.write(f"👥 フォロワー数: {metrics['followers_count']}")
                st.write(f"📝 投稿数: {metrics['tweet_count']}")
            else:
                st.warning("データが見つかりませんでした。")
        else:
            st.warning("ユーザー名を入力してください。")

with tabs[1]:
    st.info("将来的な拡張用のタブです（例：ツイート分析など）")

with tabs[2]:
    st.info("別の機能をここに追加予定です（例：スペース参加履歴など）")

import streamlit as st
import requests
from datetime import datetime
import time

# --- セットアップ ---
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANpT1wEAAAAAdsiy7QKu48ZE2ECpAeiHF3jXX%2FQ%3Dh6E0IKyk970kbBOs4dTgOGkL8pyunmPHn5shLhVx671EHydlMy"
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

# --- API取得関数（キャッシュあり） ---
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

# --- カードスタイルCSS ---
st.markdown("""
<style>
.card {
    padding: 1.5em;
    border-radius: 10px;
    background-color: #f5f8fa;
    text-align: center;
    box-shadow: 0 4px 8px rgba(0,0,0,0.1);
    margin: 10px;
}
.card-title {
    font-weight: bold;
    font-size: 1.1em;
    color: #555;
}
.card-value {
    font-size: 1.8em;
    color: #1DA1F2;
}
</style>
""", unsafe_allow_html=True)

# --- タイトルとタブ ---
st.markdown("<h1 style='color:#1DA1F2;'>X（Twitter）フォロワー追跡</h1>", unsafe_allow_html=True)

tabs = st.tabs(["アカウント情報", "拡張機能A（仮）", "拡張機能B（仮）"])

with tabs[0]:
    st.subheader("アカウント情報取得")
    with st.form("user_form"):
        username = st.text_input("X（Twitter）ユーザー名:", value="GoodAppsbyGMO")
        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("データを取得")
        with col2:
            clear = st.form_submit_button("データをクリア")

    if submitted and username:
        data = get_user_info(username)

        if "error" in data:
            st.error(f"エラー: {data['error']}")
            if "reset_time" in data:
                st.warning(f"レート制限は {data['reset_time']} に解除されます。")
        elif "data" in data:
            metrics = data["data"]["public_metrics"]
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(f"""
                <div class='card'>
                    <div class='card-title'>フォロワー数</div>
                    <div class='card-value'>{metrics['followers_count']:,}</div>
                </div>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"""
                <div class='card'>
                    <div class='card-title'>フォロー数</div>
                    <div class='card-value'>{metrics['following_count']:,}</div>
                </div>
                """, unsafe_allow_html=True)
            with c3:
                st.markdown(f"""
                <div class='card'>
                    <div class='card-title'>ツイート数</div>
                    <div class='card-value'>{metrics['tweet_count']:,}</div>
                </div>
                """, unsafe_allow_html=True)
    elif clear:
        st.experimental_rerun()

with tabs[1]:
    st.info("ここに今後の拡張機能（例：過去推移グラフ、リスト取得など）を追加予定です")

with tabs[2]:
    st.info("別の分析機能を追加予定（例：ツイート内容の分類など）")

import streamlit as st
import requests

# --- 固定設定 ---
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANpT1wEAAAAAdsiy7QKu48ZE2ECpAeiHF3jXX%2FQ%3Dh6E0IKyk970kbBOs4dTgOGkL8pyunmPHn5shLhVx671EHydlMy" 
BASE_URL = "https://api.twitter.com/2/users/by/username/"
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

# --- データ取得 ---
def get_user_info(username):
    url = f"{BASE_URL}{username}?user.fields=public_metrics"
    response = requests.get(url, headers=HEADERS)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"API error: {response.status_code}"}

# --- UI構築 ---
st.markdown("<h1 style='color:#1DA1F2;'>X（Twitter）フォロワー追跡</h1>", unsafe_allow_html=True)

with st.form("user_form"):
    st.subheader("アカウント情報取得")
    username = st.text_input("X（Twitter）ユーザー名:", value="hi_ka_yuyu")
    col1, col2 = st.columns(2)
    with col1:
        submitted = st.form_submit_button("データを取得")
    with col2:
        clear = st.form_submit_button("データをクリア")

# --- データ表示 ---
if submitted and username:
    data = get_user_info(username)
    if "error" in data:
        st.error(data["error"])
    elif "data" in data:
        user_data = data["data"]
        metrics = user_data["public_metrics"]
        
        # --- カード風に表示 ---
        st.markdown(
            """
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
            """, unsafe_allow_html=True
        )

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
    else:
        st.warning("データが取得できませんでした。")
elif clear:
    st.experimental_rerun()

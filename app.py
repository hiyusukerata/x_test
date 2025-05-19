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

# --- ChatGPT風 要約生成関数（sk-saトークンにも対応） ---
def summarize_with_raw_http(text, url):
    prompt = f"""以下の本文をもとに、X（旧Twitter）に投稿するための140文字以内の要約文を日本語で作成してください。URLも含めて制限内でお願いします。

本文:
{text}

URL: {url}
"""

    headers = {
        "Authorization": f"Bearer {st.secrets['OPENAI_API_KEY']}",
        "Content-Type": "application/json"
    }

    data = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "あなたはSNS投稿のプロです。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 200
    }

    try:
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers=headers,
            json=data
        )
        response.raise_for_status()
        content = response.json()["choices"][0]["message"]["content"].strip()
        return content
    except requests.exceptions.RequestException as e:
        return f"エラーが発生しました: {e}"

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

tabs = st.tabs(["アカウント情報", "X投稿用要約生成", "将来の拡張"])

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
    st.subheader("X投稿用 要約生成（ChatGPT API）")

    url_input = st.text_input("関連URL", placeholder="https://...")
    text_input = st.text_area("本文（長文OK）", height=200, placeholder="記事の内容や要点をここに入力")

    if st.button("要約を生成"):
        if not text_input.strip():
            st.warning("本文を入力してください。")
        else:
            with st.spinner("要約生成中..."):
                result = summarize_with_raw_http(text_input, url_input)
                st.success("要約が完了しました！")
                st.text_area("生成された投稿文（140字以内）", result, height=120)

                if st.button("Xに投稿する（ダミー）"):
                    st.info("※ 実際の投稿機能は未実装です。")

with tabs[2]:
    st.info("別の分析機能を追加予定（例：ツイート内容の分類など）")

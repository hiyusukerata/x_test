import streamlit as st
import requests
from datetime import datetime
import time
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from math import pi

# --- セットアップ ---
BEARER_TOKEN = "AAAAAAAAAAAAAAAAAAAAANpT1wEAAAAAdsiy7QKu48ZE2ECpAeiHF3jXX%2FQ%3Dh6E0IKyk970kbBOs4dTgOGkL8pyunmPHn5shLhVx671EHydlMy"
HEADERS = {"Authorization": f"Bearer {BEARER_TOKEN}"}

# --- API取得関数（キャッシュあり） ---
@st.cache_data(ttl=3600)
def get_user_info(username):
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics,description,name"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 429:
        reset_unix = int(response.headers.get("x-rate-limit-reset", time.time() + 900))
        reset_time = datetime.fromtimestamp(reset_unix).strftime('%Y-%m-%d %H:%M:%S')
        return {"error": "Rate limit exceeded", "reset_time": reset_time}
    elif response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}

    return response.json()

# --- 要約生成関数（OpenAI Chat API） ---
def summarize_text(text, url):
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
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"エラーが発生しました: {e}"

# --- レーダーチャート描画関数（個別表示・スケール統一） ---
def plot_individual_radar_chart(metrics, label, max_scale):
    categories = ['フォロワー数', 'フォロー数', 'ツイート数']
    values = [metrics['followers_count'], metrics['following_count'], metrics['tweet_count']]
    values.append(values[0])
    angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
    angles.append(angles[0])

    fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True))
    ax.plot(angles, values, label=label, color='#1DA1F2')
    ax.fill(angles, values, alpha=0.3)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=10)
    ax.set_yticks(np.linspace(0, max_scale, 5))
    ax.set_yticklabels([f"{int(x)}" for x in np.linspace(0, max_scale, 5)], fontsize=8)
    ax.set_ylim(0, max_scale)
    ax.set_title(label, size=12, pad=20)
    st.pyplot(fig)

# --- タイトルとタブ ---
st.markdown("<h1 style='color:#1DA1F2;'>X（Twitter）アカウント比較</h1>", unsafe_allow_html=True)

tabs = st.tabs(["アカウント比較", "X投稿用要約生成", "将来の拡張"])

with tabs[0]:
    st.subheader("Xアカウント情報を比較")
    with st.form("compare_form"):
        col1, col2 = st.columns(2)
        with col1:
            username1 = st.text_input("アカウント1のユーザー名", value="GoodAppsbyGMO")
        with col2:
            username2 = st.text_input("アカウント2のユーザー名", value="OpenAI")
        submitted = st.form_submit_button("比較する")

    if submitted:
        data1 = get_user_info(username1)
        data2 = get_user_info(username2)

        if "error" in data1:
            st.error(f"{username1} の取得エラー: {data1['error']}")
        if "error" in data2:
            st.error(f"{username2} の取得エラー: {data2['error']}")

        if "data" in data1 and "data" in data2:
            user1 = data1["data"]
            user2 = data2["data"]
            metrics1 = user1["public_metrics"]
            metrics2 = user2["public_metrics"]

            st.markdown("### 👤 アカウント基本情報")
            df_info = pd.DataFrame({
                "項目": ["アカウント名", "ユーザー名", "プロフィール文"],
                username1: [user1["name"], username1, user1.get("description", "(bioなし)")],
                username2: [user2["name"], username2, user2.get("description", "(bioなし)")]
            })
            st.dataframe(df_info, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### 📊 数値比較")
            df_metrics = pd.DataFrame({
                "項目": ["フォロワー数", "フォロー数", "ツイート数"],
                username1: [metrics1['followers_count'], metrics1['following_count'], metrics1['tweet_count']],
                username2: [metrics2['followers_count'], metrics2['following_count'], metrics2['tweet_count']]
            })
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)

            st.markdown("---")
            st.markdown("### 📈 レーダーチャート（アカウント別）")
            max_scale = max(
                max(metrics1['followers_count'], metrics1['following_count'], metrics1['tweet_count']),
                max(metrics2['followers_count'], metrics2['following_count'], metrics2['tweet_count'])
            ) * 1.1
            col1, col2 = st.columns(2)
            with col1:
                plot_individual_radar_chart(metrics1, username1, max_scale)
            with col2:
                plot_individual_radar_chart(metrics2, username2, max_scale)

with tabs[1]:
    st.subheader("X投稿用 要約生成（ChatGPT API）")
    url_input = st.text_input("関連URL", placeholder="https://...")
    text_input = st.text_area("本文（長文OK）", height=200, placeholder="記事の内容や要点をここに入力")

    if st.button("要約を生成"):
        if not text_input.strip():
            st.warning("本文を入力してください。")
        else:
            with st.spinner("要約生成中..."):
                result = summarize_text(text_input, url_input)
                st.success("要約が完了しました！")
                st.text_area("生成された投稿文（140字以内）", result, height=120)

                if st.button("Xに投稿する（ダミー）"):
                    st.info("※ 実際の投稿機能は未実装です。")

with tabs[2]:
    st.info("別の分析機能を追加予定（例：ツイート内容の分類など）")

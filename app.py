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

# --- レーダーチャート描画関数 ---
def plot_radar_chart(metrics1, metrics2, label1, label2):
    categories = ['フォロワー数', 'フォロー数', 'ツイート数']
    values1 = [metrics1['followers_count'], metrics1['following_count'], metrics1['tweet_count']]
    values2 = [metrics2['followers_count'], metrics2['following_count'], metrics2['tweet_count']]

    max_val = max(values1 + values2) * 1.1
    values1.append(values1[0])
    values2.append(values2[0])
    angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
    angles.append(angles[0])

    fig, ax = plt.subplots(figsize=(5, 5), subplot_kw=dict(polar=True))
    ax.plot(angles, values1, label=label1)
    ax.fill(angles, values1, alpha=0.25)
    ax.plot(angles, values2, label=label2)
    ax.fill(angles, values2, alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_yticklabels([])
    ax.set_ylim(0, max_val)
    ax.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
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
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{user1['name']} (@{username1})**")
                st.markdown(user1.get("description", "(bioなし)"))
            with col2:
                st.markdown(f"**{user2['name']} (@{username2})**")
                st.markdown(user2.get("description", "(bioなし)"))

            st.markdown("### 📊 数値比較")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("フォロワー数", f"{metrics1['followers_count']:,}")
                st.metric("フォロー数", f"{metrics1['following_count']:,}")
                st.metric("ツイート数", f"{metrics1['tweet_count']:,}")
            with col2:
                st.metric("フォロワー数", f"{metrics2['followers_count']:,}")
                st.metric("フォロー数", f"{metrics2['following_count']:,}")
                st.metric("ツイート数", f"{metrics2['tweet_count']:,}")

            st.markdown("### 📈 レーダーチャート比較")
            plot_radar_chart(metrics1, metrics2, username1, username2)

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

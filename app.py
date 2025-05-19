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
    url = f"https://api.twitter.com/2/users/by/username/{username}?user.fields=public_metrics"
    response = requests.get(url, headers=HEADERS)

    if response.status_code == 429:
        reset_unix = int(response.headers.get("x-rate-limit-reset", time.time() + 900))
        reset_time = datetime.fromtimestamp(reset_unix).strftime('%Y-%m-%d %H:%M:%S')
        return {"error": "Rate limit exceeded", "reset_time": reset_time}
    elif response.status_code != 200:
        return {"error": f"API error: {response.status_code}"}

    return response.json()

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
            metrics1 = data1["data"]["public_metrics"]
            metrics2 = data2["data"]["public_metrics"]

            st.markdown("### 📊 数値比較")
            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"**{username1}**")
                st.metric("フォロワー数", f"{metrics1['followers_count']:,}")
                st.metric("フォロー数", f"{metrics1['following_count']:,}")
                st.metric("ツイート数", f"{metrics1['tweet_count']:,}")
            with col2:
                st.markdown(f"**{username2}**")
                st.metric("フォロワー数", f"{metrics2['followers_count']:,}")
                st.metric("フォロー数", f"{metrics2['following_count']:,}")
                st.metric("ツイート数", f"{metrics2['tweet_count']:,}")

            st.markdown("### 📈 レーダーチャート比較")
            plot_radar_chart(metrics1, metrics2, username1, username2)

with tabs[1]:
    st.info("要約生成機能はこの後実装します。")

with tabs[2]:
    st.info("別の分析機能を追加予定（例：ツイート内容の分類など）")

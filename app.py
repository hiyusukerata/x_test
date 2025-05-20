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

# --- 相対スコア評価（10段階） ---
def calculate_relative_scores(metrics1, metrics2):
    scores1 = []
    scores2 = []
    for key in ['followers_count', 'following_count', 'tweet_count']:
        val1 = metrics1[key]
        val2 = metrics2[key]
        total = val1 + val2 if (val1 + val2) > 0 else 1
        ratio1 = val1 / total
        ratio2 = val2 / total
        scores1.append(max(1, round(ratio1 * 10)))
        scores2.append(max(1, round(ratio2 * 10)))
    return scores1, scores2

# --- レーダーチャート描画関数（英語カテゴリ名・10段階スコア） ---
def plot_relative_chart(scores, label):
    categories = ['followers', 'following', 'posts']
    scores += scores[:1]
    angles = [n / float(len(categories)) * 2 * pi for n in range(len(categories))]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(4.5, 4.5), subplot_kw=dict(polar=True))
    ax.plot(angles, scores, color='#1DA1F2', linewidth=2)
    ax.fill(angles, scores, color='#1DA1F2', alpha=0.25)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories, fontsize=9)
    ax.set_yticks(range(1, 11))
    ax.set_yticklabels([str(i) for i in range(1, 11)], fontsize=8)
    ax.set_ylim(0, 10)
    return fig

# --- タイトルとタブ ---
st.markdown("<h1 style='color:#1DA1F2;'>X（Twitter）アカウント比較</h1>", unsafe_allow_html=True)

tabs = st.tabs(["アカウント比較", "X投稿用要約生成", "予約投稿"])

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
            scores1, scores2 = calculate_relative_scores(metrics1, metrics2)
            chart1 = plot_relative_chart(scores1, username1)
            chart2 = plot_relative_chart(scores2, username2)
            col1, col2 = st.columns(2)
            with col1:
                st.pyplot(chart1)
            with col2:
                st.pyplot(chart2)

            st.markdown("### 📊 数値比較")
            df_metrics = pd.DataFrame({
                "項目": ["フォロワー数", "フォロー数", "ツイート数"],
                username1: [metrics1['followers_count'], metrics1['following_count'], metrics1['tweet_count']],
                username2: [metrics2['followers_count'], metrics2['following_count'], metrics2['tweet_count']]
            })
            st.dataframe(df_metrics, use_container_width=True, hide_index=True)

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

# Tab2: スケジュールベースの投稿予約（モック）

with tabs[2]:
    import streamlit as st
    import calendar
    import json
    import os
    from datetime import date, timedelta, datetime as dt
    import streamlit.components.v1 as components

    st.subheader("🗓 スケジュールベースの投稿予約（モック）")

    
    if st.button("📆 Googleカレンダーと連携（モック）"):
    st.info("Googleカレンダーとの連携機能は現在モックです。")


    today = date.today()

    if "calendar_year" not in st.session_state:
        st.session_state.calendar_year = today.year
    if "calendar_month" not in st.session_state:
        st.session_state.calendar_month = today.month

    col_prev, col_info, col_next = st.columns([1, 3, 1])
    with col_prev:
        if st.button("◀ 前月"):
            if st.session_state.calendar_month == 1:
                st.session_state.calendar_month = 12
                st.session_state.calendar_year -= 1
            else:
                st.session_state.calendar_month -= 1
    with col_info:
        year = st.session_state.calendar_year
        month = st.session_state.calendar_month
        st.markdown(f"### {year}年 {month}月")
    with col_next:
        if st.button("次月 ▶"):
            if st.session_state.calendar_month == 12:
                st.session_state.calendar_month = 1
                st.session_state.calendar_year += 1
            else:
                st.session_state.calendar_month += 1

    cal = calendar.Calendar()

    if "event_data" not in st.session_state:
        if os.path.exists("events.json"):
            with open("events.json", "r", encoding="utf-8") as f:
                st.session_state.event_data = json.load(f)
        else:
            st.session_state.event_data = {}

    if "selected_date" not in st.session_state:
        st.session_state.selected_date = today.strftime("%Y-%m-%d")

    def get_default_events(y, m):
        default = {}
        for d in range(1, 32):
            try:
                current_date = date(y, m, d)
                key = current_date.strftime("%Y-%m-%d")
                events = []
                if current_date.weekday() in [1, 4]:
                    events.append("ドリンク1杯無料デー")
                if d % 5 == 0:
                    events.append("10%オフデー")
                default[key] = events
            except:
                continue
        return default

    default_events = get_default_events(year, month)
    all_events = {**default_events}
    for k, v in st.session_state.event_data.items():
        all_events.setdefault(k, []).extend(v)

    def build_calendar():
        html = "<table style='border-collapse: collapse; width: 100%; text-align: center;'>"
        html += "<tr>" + "".join([f"<th style='padding: 4px'>{w}</th>" for w in ['日', '月', '火', '水', '木', '金', '土']]) + "</tr>"
        for week in cal.monthdayscalendar(year, month):
            html += "<tr>"
            for day in week:
                if day == 0:
                    html += "<td></td>"
                else:
                    d_str = f"{year}-{month:02d}-{day:02d}"
                    js = f"window.parent.postMessage('{d_str}','*')"
                    style = "padding:6px; border:1px solid #ccc; font-size: 13px; cursor: pointer;"
                    content = f"{day}"
                    if d_str == today.strftime("%Y-%m-%d"):
                        style += " background-color:#1DA1F2; color:white; font-weight:bold;"
                    dot = "<div style='font-size: 8px; color: black;'>●</div>" if d_str in all_events and all_events[d_str] else ""
                    html += f"<td onclick=\"{js}\" style='{style}'>{content}{dot}</td>"
            html += "</tr>"
        html += "</table>"
        return html

    selected_day = components.html(
        f"""
        <script>
        window.addEventListener("message", (e) => {{
            const d = e.data;
            const streamlitEvent = new CustomEvent("streamlit:setComponentValue", {{ detail: d }});
            document.dispatchEvent(streamlitEvent);
        }});
        </script>
        {build_calendar()}
        """,
        height=330
    )

    if selected_day and isinstance(selected_day, str):
        st.session_state.selected_date = selected_day

    selected_date = st.text_input("イベントを確認・追加する日付 (YYYY-MM-DD)", value=st.session_state.selected_date)
    st.session_state.selected_date = selected_date

    st.markdown(f"#### 📅 {selected_date} のイベント")
    current_events = all_events.get(selected_date, [])
    if current_events:
        for i, ev in enumerate(current_events):
            st.write(f"{i+1}. {ev}")
        delete_idx = st.number_input("削除したいイベント番号（上記リストの番号）", min_value=0, max_value=len(current_events), value=0)
        if st.button("選択イベントを削除") and delete_idx > 0:
            del_event = current_events[delete_idx - 1]
            if selected_date in st.session_state.event_data and del_event in st.session_state.event_data[selected_date]:
                st.session_state.event_data[selected_date].remove(del_event)
                with open("events.json", "w", encoding="utf-8") as f:
                    json.dump(st.session_state.event_data, f, ensure_ascii=False, indent=2)
                st.success(f"イベント「{del_event}」を削除しました")
    else:
        st.write("この日にはイベントがありません。")

    new_event = st.text_input("新しいイベントを追加")
    if st.button("イベントを追加"):
        if new_event.strip():
            st.session_state.event_data.setdefault(selected_date, []).append(new_event.strip())
            with open("events.json", "w", encoding="utf-8") as f:
                json.dump(st.session_state.event_data, f, ensure_ascii=False, indent=2)
            st.success("イベントを追加しました")

    # --- 宣伝文テンプレート ---
    st.markdown("---")
    st.markdown("### ✍ 宣伝文テンプレート（選択日ベース）")

    if selected_date in all_events and all_events[selected_date]:
        event = all_events[selected_date][0]
        dt_obj = dt.strptime(selected_date, "%Y-%m-%d")
        month_str = dt_obj.strftime("%m")
        day_str = dt_obj.strftime("%d")

        options = [
            f"{month_str}月{day_str}日は{event}！みなさまのご来店をお待ちしております。",
            f"{month_str}月{day_str}日は{event}！乞うご期待！！",
            f"{month_str}月{day_str}日は{event}！いつもにまして店長気合い入ってます！ぜひご来店ください！"
        ]
        selected_option = st.radio("宣伝文候補を選択：", options, key="selected_ad_text")

        # --- 予約投稿設定 ---
        st.markdown("---")
        st.markdown("### ⏰ 予約投稿設定")
        default_time = dt.now() + timedelta(hours=1)
        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            y = st.number_input("年", value=default_time.year, step=1)
        with col2:
            m = st.number_input("月", min_value=1, max_value=12, value=default_time.month, step=1)
        with col3:
            d = st.number_input("日", min_value=1, max_value=31, value=default_time.day, step=1)
        with col4:
            h = st.number_input("時", min_value=0, max_value=23, value=default_time.hour, step=1)
        with col5:
            mi = st.number_input("分", min_value=0, max_value=59, value=0, step=1)

        if st.button("予約投稿する"):
            post_time = f"{y}年{m:02d}月{d:02d}日 {h:02d}:{mi:02d}:00"
            st.session_state.reservation_check = True
            st.session_state.reservation_text = selected_option
            st.session_state.reservation_time = post_time

    # --- 予約確認表示 ---
    if st.session_state.get("reservation_check"):
        st.info(f"{st.session_state.reservation_time} に以下の投稿を予約しますか？")
        st.code(st.session_state.reservation_text)

        col_confirm1, col_confirm2 = st.columns([1, 1])
        with col_confirm1:
            if st.button("✅ はい（予約）"):
                st.success("予約投稿を受け付けました（仮）")
                st.session_state.reservation_check = False
        with col_confirm2:
            if st.button("❌ いいえ（キャンセル）"):
                st.warning("予約をキャンセルしました")
                st.session_state.reservation_check = False
    else:
        st.session_state.reservation_check = False

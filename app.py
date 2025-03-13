import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from supabase import create_client, Client
from matplotlib import rcParams

url: str = "https://ioossmpojhpcevysvgcl.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlvb3NzbXBvamhwY2V2eXN2Z2NsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzNTczMjksImV4cCI6MjA1NTkzMzMyOX0.8QnKrqGgiZ3dLoYNqamb6u4QdhDDD9oe-QlsB77lqy8"
supabase: Client = create_client(url, key)
response = supabase.table("wait_data").select("*").neq("time", -1).limit(50000).execute()
rcParams['font.family'] = 'MS Gothic'



df = pd.DataFrame(response.data)
df["saved_at"] = pd.to_datetime(df["saved_at"], utc=True).dt.tz_convert("Asia/Tokyo")

df["date"] = df["saved_at"].dt.date
df["weekday"] = df["saved_at"].dt.day_name()

# Streamlit UI
st.title('炭焼きレストランさわやか 待ち時間')
st.sidebar.header('フィルタ設定')

# 今日の日付
today_date = pd.Timestamp.today().date()

# 日にち選択
selected_date = st.sidebar.selectbox('比較する日を選択してください:', df['date'].unique(), index=list(df['date'].unique()).index(today_date) if today_date in df['date'].unique() else 0)

# 場所選択
selected_place = st.sidebar.selectbox('場所を選択してください:', df['place'].unique())

# 比較する場所選択
comparison_places = st.sidebar.multiselect('比較する場所を選択してください:', [p for p in df['place'].unique() if p != selected_place])

# 時間範囲選択
start_time = st.sidebar.slider('開始時間を選択してください:', 0, 23, 0, 1)
end_time = st.sidebar.slider('終了時間を選択してください:', 0, 23, 23, 1)

# データのフィルタリング
df_selected_date = df[df["date"] == selected_date]
df_today = df[df["date"] == today_date]

df_selected = df_selected_date[df_selected_date["place"] == selected_place]
df_comparison = df_selected_date[df_selected_date["place"].isin(comparison_places)]
df_today_selected = df_today[df_today["place"] == selected_place]

# 時間の計算
for d in [df_selected, df_comparison, df_today_selected]:
    d["hour"] = d["saved_at"].dt.hour + d["saved_at"].dt.minute / 60.0

# 時間範囲で絞り込み
df_selected = df_selected[(df_selected["hour"] >= start_time) & (df_selected["hour"] <= end_time)]
df_comparison = df_comparison[(df_comparison["hour"] >= start_time) & (df_comparison["hour"] <= end_time)]
df_today_selected = df_today_selected[(df_today_selected["hour"] >= start_time) & (df_today_selected["hour"] <= end_time)]

# === グラフ 1: 選択した日 vs 今日の待ち時間 ===
if len(df_selected) > 0 or len(df_today_selected) > 0:
    st.subheader(f'{selected_date} vs 今日 ({today_date}) - {selected_place} - 時間範囲: {start_time}-{end_time}h')
    fig, ax = plt.subplots(figsize=(10, 6))

    # 選択した日
    if len(df_selected) > 0:
        df_selected = df_selected.sort_values(by="hour")
        ax.plot(df_selected["hour"], df_selected["time"], marker="o", linestyle="--", color="blue", label=f"{selected_date} (選択日)")

    # 今日
    if len(df_today_selected) > 0:
        df_today_selected = df_today_selected.sort_values(by="hour")
        ax.plot(df_today_selected["hour"], df_today_selected["time"], marker="o", linestyle="-", color="red", label=f"{today_date} (今日)")

    ax.set_xlabel("時間")
    ax.set_ylabel("待ち時間")
    ax.grid(True)
    ax.legend(title='比較対象')
    st.pyplot(fig)

# === グラフ 2: 選択した場所 vs 比較する場所 ===
if len(df_selected) > 0:
    st.subheader(f'{selected_date} - {selected_place} vs {", ".join(comparison_places)} - 時間範囲: {start_time}-{end_time}h')
    fig, ax = plt.subplots(figsize=(10, 6))

    # 選択した場所
    df_selected = df_selected.sort_values(by="hour")
    ax.plot(df_selected["hour"], df_selected["time"], marker="o", linestyle="-", label=f"{selected_place} (選択)")

    # 比較する場所
    for place in comparison_places:
        df_place = df_comparison[df_comparison["place"] == place]
        df_place = df_place.sort_values(by="hour")
        ax.plot(df_place["hour"], df_place["time"], marker="o", linestyle="-", label=place)

    ax.set_xlabel("時間")
    ax.set_ylabel("待ち時間")
    ax.grid(True)
    ax.legend(title='場所')
    st.pyplot(fig)

# === 10分ごとの待ち時間の表（最新7日間） ===
def round_time(dt):
    return dt.replace(minute=(dt.minute // 10) * 10, second=0)

df["time_10min"] = df["saved_at"].apply(round_time).dt.strftime("%H:%M")

# 最新7日間のデータ取得
days = sorted(df["date"].unique())[-7:]
df_weekly = df[df["date"].isin(days) & (df["place"] == selected_place)]
weekly_pivot = df_weekly.pivot_table(index="time_10min", columns="date", values="time", aggfunc="mean")
weekly_pivot = weekly_pivot[days]  # 日付順を統一

# 表のスタイル設定
st.subheader(f"{selected_place} の最新7日間の待ち時間（10分ごと）")
if not weekly_pivot.empty:
    styled_table = weekly_pivot.style.background_gradient(cmap="coolwarm", axis=None).format("{:.1f} 分")
    st.dataframe(styled_table)
else:
    st.write("データがありません。")

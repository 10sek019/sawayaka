import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st
from supabase import create_client, Client
from matplotlib import rcParams

url: str = "https://ioossmpojhpcevysvgcl.supabase.co"
key: str = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imlvb3NzbXBvamhwY2V2eXN2Z2NsIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NDAzNTczMjksImV4cCI6MjA1NTkzMzMyOX0.8QnKrqGgiZ3dLoYNqamb6u4QdhDDD9oe-QlsB77lqy8"
supabase: Client = create_client(url, key)
response = supabase.table("wait_data").select("*").neq("time", -1).limit(20000).execute()
rcParams['font.family'] = 'MS Gothic'

df = pd.DataFrame(response.data)
df["saved_at"] = pd.to_datetime(df["saved_at"], utc=True).dt.tz_convert("Asia/Tokyo")

df["date"] = df["saved_at"].dt.date  # 日付を新しい列に保存
df["weekday"] = df["saved_at"].dt.day_name()  # 曜日を新しい列に保存

# Streamlit UIの作成
st.title('インタラクティブなデータフィルタリングとプロット')
st.sidebar.header('フィルタ設定')

# 日にち選択（曜日ではなく日にちを選択）
selected_date = st.sidebar.selectbox('日にちを選択してください:', df['date'].unique())

# 複数の場所選択
selected_places = st.sidebar.multiselect('場所を選択してください:', df['place'].unique(), default=df['place'].unique())

# 時間範囲選択
start_time = st.sidebar.slider('開始時間を選択してください:', 0, 23, 0, 1)
end_time = st.sidebar.slider('終了時間を選択してください:', 0, 23, 23, 1)

# データのフィルタリング
df_day = df[df["date"] == selected_date]  # 日付でフィルタリング
df_day_place = df_day[df_day["place"].isin(selected_places)]  # 複数の場所でフィルタリング

# 時間の計算
df_day_place["hour"] = df_day_place["saved_at"].dt.hour + df_day_place["saved_at"].dt.minute / 60.0

# 時間範囲で絞り込み
df_filtered = df_day_place[(df_day_place["hour"] >= start_time) & (df_day_place["hour"] <= end_time)]

if len(df_filtered) > 0:
    # グラフの描画
    st.subheader(f'{selected_date} ({", ".join(selected_places)}) - 時間範囲: {start_time}-{end_time}h')
    fig, ax = plt.subplots(figsize=(10, 6))
    
    # 場所ごとにデータをグループ化して、各場所ごとに線を描画
    for place in selected_places:
        df_place = df_filtered[df_filtered["place"] == place]
        df_place = df_place.sort_values(by="hour") 
        ax.plot(df_place["hour"], df_place["time"], marker="o", linestyle="-", label=place)

    # ax.set_title(f"{selected_date} ({', '.join(selected_places)}) - 時間範囲: {start_time}-{end_time}h")
    ax.set_xlabel("時間")
    ax.set_ylabel("待ち")
    ax.grid(True)
    plt.xticks()
    ax.legend(title='場所')  # 凡例を追加
    st.pyplot(fig)
else:
    st.write("選択された条件に一致するデータはありません。")

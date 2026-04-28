import streamlit as st
import urllib.parse

# --- アプリの基本設定 ---
st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")
st.write("目的地を入力して、最適なルートをGoogleマップで確認しましょう。")

# --- サイドバー：設定（判定の目安として残す） ---
st.sidebar.header("⚙️ 設定")
car_type = st.sidebar.radio("車種", ["普通車", "軽自動車"])
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)
st.sidebar.info(f"あなたの基準: {threshold}円/分\n(1時間で {threshold*60}円)")

# --- メイン画面：ルート入力 ---
st.subheader("📍 ルート設定")

col_a, col_b = st.columns(2)
with col_a:
    start_p = st.text_input("出発地", "東京駅")
with col_b:
    end_p = st.text_input("目的地", "箱根湯本駅")

# 経由地
with st.expander("＋ 経由地を追加する"):
    w1 = st.text_input("経由地1", "")
    w2 = st.text_input("経由地2", "")
    w3 = st.text_input("経由地3", "")

# --- Googleマップ連携ボタン ---
st.divider()
st.subheader("🗺️ ナビを起動")

def create_gmaps_url(start, end, waypoints):
    base_url = "https://www.google.com/maps/dir/"
    # パス形式でURLを作成: /出発地/経由地1/経由地2/.../目的地
    path_elements = [start]
    for w in waypoints:
        if w:
            path_elements.append(w)
    path_elements.append(end)
    
    # URLエンコードして結合
    encoded_path = "/".join([urllib.parse.quote(p) for p in path_elements])
    return base_url + encoded_path

gmaps_url = create_gmaps_url(start_p, end_p, [w1, w2, w3])

st.link_button("🚀 Googleマップでルートを比較する", gmaps_url, use_container_width=True)

# --- 使い方のヒント ---
st.divider()
st.caption("💡 使い方アドバイス")
st.info(f"""
1. 上のボタンでGoogleマップを開く
2. 「高速ルート」と「下道ルート」の時間を比較する
3. **時間の差(分) × {threshold}円** を計算！
   → これが高速代より高ければ、高速に乗る価値アリです！
""")

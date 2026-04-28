import streamlit as st
import urllib.parse

# --- アプリの基本設定 ---
st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route (タコ・ルート)")
st.write("コスパ・タイパ最適化ナビ & Googleマップ連携")

# --- サイドバー：ユーザー設定 ---
st.sidebar.header("1. 基本設定")
car_type = st.sidebar.radio("車種を選択", ["普通車", "軽自動車"])
is_discount = st.sidebar.checkbox("休日・深夜割引 (30%OFF)")

st.sidebar.divider()
st.sidebar.header("2. あなたの基準")
threshold = st.sidebar.slider("1分短縮に何円まで払えますか？", 0, 100, 25)

# --- メイン画面：ルート詳細入力 ---
st.subheader("📍 どこへ行きますか？")

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
st.subheader("🔗 外部マップ連携")

# GoogleマップのURLを生成するロジック
def create_gmaps_url(start, end, waypoints):
    base_url = "https://www.google.com/maps/dir/?api=1"
    params = {
        "origin": start,
        "destination": end,
        "travelmode": "driving"
    }
    # 経由地がある場合に追加
    actual_waypoints = [w for w in waypoints if w]
    if actual_waypoints:
        params["waypoints"] = "|".join(actual_waypoints)
    
    return base_url + "&" + urllib.parse.urlencode(params)

gmaps_url = create_gmaps_url(start_p, end_p, [w1, w2, w3])

# ボタンの設置
st.link_button("🗺️ Googleマップでルートを確認", gmaps_url, use_container_width=True)

st.divider()

# --- タイパ計算セクション ---
st.subheader("⏱️ タイパ判定（手動入力）")
st.caption("Googleマップで表示された「距離」と「短縮時間」を入力してください。")

col1, col2 = st.columns(2)
with col1:
    dist_km = st.number_input("高速区間の距離 (km)", min_value=0.0, value=50.0)
with col2:
    time_saved = st.number_input("高速での短縮時間 (分)", min_value=1, value=30)

# 料金計算 (28円/km + 150円)
raw_toll = (dist_km * 28) + 150
car_factor = 0.8 if car_type == "軽自動車" else 1.0
discount_factor = 0.7 if is_discount else 1.0
estimated_toll = int(raw_toll * car_factor * discount_factor)

# タイパ単価
cost_per_min = estimated_toll / time_saved if time_saved > 0 else 0

# 判定表示
if cost_per_min <= threshold:
    st.success(f"✅ 高速推奨！ (1分あたり {cost_per_min:.1f}円)")
    st.progress(min(cost_per_min / 100, 1.0))
else:
    st.warning(f"🛑 下道推奨 (1分あたり {cost_per_min:.1f}円)")
    st.progress(min(cost_per_min / 100, 1.0))

st.metric("概算高速料金", f"{estimated_toll} 円")

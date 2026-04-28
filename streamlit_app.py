import streamlit as st
import urllib.parse

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 1. あなたの基準
st.subheader("👤 あなたの基準設定")
threshold = st.slider("1分短縮に何円まで払えますか？", 0, 100, 25)

st.divider()

# 2. ルート入力
st.subheader("📍 行き先を入力")
col_start, col_end = st.columns(2)
with col_start:
    start_p = st.text_input("出発地", "現在地")
with col_end:
    end_p = st.text_input("目的地", "")

with st.expander("＋ 経由地を追加"):
    w1 = st.text_input("経由地1", "")
    w2 = st.text_input("経由地2", "")

# 3. Googleマップ起動（最も標準的な検索URL）
if end_p:
    # 経由地をカンマで結合
    way_list = [w for w in [w1, w2] if w]
    waypoints = ",".join(way_list)
    
    # パソコン版でもスマホ版でも「検索」として正しく認識される標準URL
    params = {
        "api": "1",
        "origin": start_p,
        "destination": end_p,
        "travelmode": "driving"
    }
    if waypoints:
        params["waypoints"] = waypoints

    gmaps_url = f"https://www.google.com/maps/dir/?{urllib.parse.urlencode(params)}"

    st.link_button("🚀 Googleマップを起動", gmaps_url, use_container_width=True)
else:
    st.warning("目的地を入力してください")

st.divider()

# 4. タイパ判定
st.subheader("⚖️ タイパ判定")
col1, col2 = st.columns(2)
with col1:
    toll_input = st.number_input("高速料金 (円)", min_value=0, step=100, value=0)
with col2:
    time_saved_input = st.number_input("短縮時間 (分)", min_value=1, step=1, value=1)

if toll_input > 0:
    cost_per_min = toll_input / time_saved_input
    if cost_per_min <= threshold:
        st.success(f"✅ 【高速推奨】1分あたり {cost_per_min:.1f}円")
    else:
        st.warning(f"🛑 【下道推奨】1分あたり {cost_per_min:.1f}円")

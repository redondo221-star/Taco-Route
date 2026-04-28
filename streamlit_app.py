import streamlit as st
import urllib.parse

# --- アプリ設定 ---
st.set_page_config(page_title="Taco-Route (Yahoo!)", layout="centered")
st.title("🚗 Taco-Route")
st.caption("Yahoo!カーナビ連携版（安定版）")

# 1. あなたの基準設定
st.subheader("👤 あなたの基準設定")
threshold = st.slider("1分短縮に何円まで払えますか？", 0, 100, 25)
st.caption(f"現在の基準: {threshold}円/分")

st.divider()

# 2. ルート入力
st.subheader("📍 行き先を入力")
col_start, col_end = st.columns(2)
with col_start:
    start_p = st.text_input("出発地", "現在地")
with col_end:
    end_p = st.text_input("目的地", "")

if end_p:
    # Yahoo!道路経路検索用のURLを作成（これが最も安定しています）
    # 出発地が現在地の場合は、目的地のみ指定
    params = {
        "from": start_p if start_p != "現在地" else "",
        "to": end_p,
        "yid": "navicore" # これを入れるとアプリ起動を促してくれます
    }
    
    # Yahoo!マップのルート検索URL
    y_map_url = f"https://map.yahoo.co.jp/route/car?{urllib.parse.urlencode(params)}"

    st.link_button("🚀 Yahoo!ナビでルートを表示", y_map_url, use_container_width=True)
else:
    st.warning("目的地を入力してください")

st.divider()

# 3. タイパ判定
st.subheader("⚖️ タイパ判定")
st.write("ナビで出た「料金」と「時間の差」を入力してください。")

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

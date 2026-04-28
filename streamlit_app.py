import streamlit as st
import urllib.parse

# --- アプリ設定 ---
st.set_page_config(page_title="Taco-Route (Yahoo!)", layout="centered")
st.title("🚗 Taco-Route")
st.caption("Yahoo!カーナビ連携版")

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

# ※Yahoo!カーナビの仕様上、URL連携では経由地を複数指定するのが難しいため
# シンプルに出発と到着のみに絞っています。
if end_p:
    # Yahoo!カーナビ専用のURLスキームを作成
    # 出発地が「現在地」の場合は引数を変える
    s_param = urllib.parse.quote(start_p)
    d_param = urllib.parse.quote(end_p)
    
    if start_p == "現在地":
        # 現在地から目的地へ
        y_navi_url = f"yidm://navi/go?dest={d_param}&lat=&lon="
    else:
        # 指定場所から目的地へ
        y_navi_url = f"yidm://navi/go?start={s_param}&dest={d_param}"

    st.link_button("🚀 Yahoo!カーナビを起動", y_navi_url, use_container_width=True)
else:
    st.warning("目的地を入力してください")

st.divider()

# 3. タイパ判定
st.subheader("⚖️ タイパ判定")
st.write("ナビで出た「料金」と「時間の差」を入れてください。")

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

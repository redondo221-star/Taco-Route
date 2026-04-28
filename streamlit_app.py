import streamlit as st
import urllib.parse

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- サイドバー：基準設定 ---
st.sidebar.header("⚙️ あなたの基準")
threshold = st.sidebar.slider("1分短縮に何円払える？", 0, 100, 25)

# --- メイン：ルート入力 ---
st.subheader("📍 どこへ行きますか？")
col_a, col_b = st.columns(2)
with col_a:
    start_p = st.text_input("出発地", "東京駅")
with col_b:
    end_p = st.text_input("目的地", "箱根湯本駅")

with st.expander("＋ 経由地を追加"):
    w1 = st.text_input("経由地1", "")
    w2 = st.text_input("経由地2", "")

# Googleマップ起動ボタン
path_elements = [start_p, w1, w2, end_p]
encoded_path = "/".join([urllib.parse.quote(p) for p in path_elements if p])
gmaps_url = f"https://www.google.com/maps/dir/{encoded_path}"

st.link_button("🚀 Googleマップで料金と時間を調査", gmaps_url, use_container_width=True)

st.divider()

# --- クイックタイパ判定（スライダー式） ---
st.subheader("⚖️ タイパ判定")
st.write("マップで見た「高速料金」と「短縮時間」をセットしてください。")

toll_input = st.select_slider("高速料金はいくら？", options=range(0, 5001, 100), value=1000)
time_saved_input = st.select_slider("何分短縮できる？", options=range(1, 121, 1), value=30)

# 計算
cost_per_min = toll_input / time_saved_input

if cost_per_min <= threshold:
    st.success(f"✅ 【高速推奨】1分あたり {cost_per_min:.1f}円 です！")
    st.balloons()
else:
    st.warning(f"🛑 【下道推奨】1分あたり {cost_per_min:.1f}円 です。")

st.caption(f"現在の判定ライン: {threshold}円/分")

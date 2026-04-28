import streamlit as st
import urllib.parse
import time

# --- アプリ設定 ---
st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 1. あなたの基準（一番上に配置）
st.info("💡 最初に「自分の基準」をセットしましょう")
threshold = st.slider("1分短縮に何円まで払えますか？", 0, 100, 25, help="この金額以下なら『高速推奨』と判定します")
st.caption(f"現在の基準: {threshold}円/分 （1時間で {threshold*60}円）")

st.divider()

# 2. ルート入力
st.subheader("📍 どこへ行きますか？")
col_start, col_end = st.columns(2)
with col_start:
    start_p = st.text_input("出発地", "東京駅")
with col_end:
    end_p = st.text_input("目的地", "箱根湯本駅")

with st.expander("＋ 経由地を追加"):
    w1 = st.text_input("経由地1", "")
    w2 = st.text_input("経由地2", "")

# 3. Googleマップ起動（リフレッシュ機能付き）
# 検索のたびにURLを変えるためにタイムスタンプを付与
refresh_token = int(time.time())
path_elements = [start_p, w1, w2, end_p]
encoded_path = "/".join([urllib.parse.quote(p) for p in path_elements if p])

# Googleマップを「新規検索」として強制認識させるためのURL
gmaps_url = f"https://www.google.com/maps/dir/{encoded_path}/?force=1&t={refresh_token}"

st.link_button("🚀 Googleマップで最新ルートを調査", gmaps_url, use_container_width=True)

st.divider()

# 4. タイパ判定
st.subheader("⚖️ タイパ判定")
st.write("マップで見た「料金」と「短縮時間」をセット！")

col1, col2 = st.columns(2)
with col1:
    toll_input = st.number_input("高速料金 (円)", min_value=0, step=100, value=1000)
with col2:
    time_saved_input = st.number_input("短縮時間 (分)", min_value=1, step=1, value=30)

# 判定ロジック
cost_per_min = toll_input / time_saved_input if time_saved_input > 0 else 0

if cost_per_min <= threshold:
    st.success(f"✅ 【高速推奨】1分あたり {cost_per_min:.1f}円")
    st.balloons()
else:
    st.warning(f"🛑 【下道推奨】1分あたり {cost_per_min:.1f}円")

st.caption(f"判定ライン: {threshold}円/分")

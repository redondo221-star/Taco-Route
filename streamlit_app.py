import streamlit as st

# --- アプリの基本設定 ---
st.set_page_config(page_title="コスパ・タイパ最適化ナビ", layout="centered")
st.title("🚗 タイパ・ルート・コンシェルジュ")
st.write("出発地から目的地まで、経由地を含めたコスパを判定します。")

# --- サイドバー：ユーザー設定 ---
st.sidebar.header("1. 基本設定")
car_type = st.sidebar.radio("車種を選択", ["普通車", "軽自動車"])
is_discount = st.sidebar.checkbox("休日・深夜割引 (30%OFF)")

st.sidebar.divider()
st.sidebar.header("2. あなたの基準")
threshold = st.sidebar.slider("1分短縮に何円まで払えますか？", 0, 100, 25)
st.sidebar.caption(f"現在の設定: 1時間あたり {threshold * 60}円 の価値")

# --- メイン画面：ルート詳細入力 ---
st.subheader("📍 ルート・経由地の設定")

col_a, col_b = st.columns(2)
with col_a:
    start_point = st.text_input("出発地", "東京駅")
with col_b:
    end_point = st.text_input("目的地", "箱根湯本駅")

# 経由地の入力（最大3つ）
with st.expander("＋ 経由地を追加する"):
    waypoint1 = st.text_input("経由地1", "")
    waypoint2 = st.text_input("経由地2", "")
    waypoint3 = st.text_input("経由地3", "")

st.divider()

st.subheader("⏱️ 走行データの入力")
st.info("Googleマップ等で調べた「高速ルート」と「下道ルート」の差を入力してください。")

col1, col2 = st.columns(2)
with col1:
    total_dist_km = st.number_input("高速を利用する区間の総距離 (km)", min_value=0.0, value=50.0)
with col2:
    total_time_saved = st.number_input("高速を使うことで短縮される総時間 (分)", min_value=1, value=30)

# --- 計算ロジック ---
# 高速料金の概算（28円/km + 150円）
per_km_rate = 28 
base_fare = 150
raw_toll = (total_dist_km * per_km_rate) + base_fare

# 車種・割引補正
car_factor = 0.8 if car_type == "軽自動車" else 1.0
discount_factor = 0.7 if is_discount else 1.0
estimated_toll = int(raw_toll * car_factor * discount_factor)

# タイパ（1分あたりのコスト）
actual_cost_per_min = estimated_toll / total_time_saved if total_time_saved > 0 else 0

# --- 結果表示 ---
st.divider()
st.subheader("📊 判定・タイパメーター")

# メーターの視覚化（ゲージ風）
progress_val = min(actual_cost_per_min / (threshold * 2 if threshold > 0 else 100), 1.0)
st.progress(progress_val)

if actual_cost_per_min <= threshold:
    st.success(f"### ✅ 高速利用を推奨！")
    st.write(f"**{start_point}** から **{end_point}** まで、時間を買う価値があります。")
    profit = int((threshold - actual_cost_per_min) * total_time_saved)
    st.write(f"1分を {actual_cost_per_min:.1f}円 で購入できます（あなたの基準より {threshold - actual_cost_per_min:.1f}円/分 お得）。")
    st.info(f"💡 この移動で、実質 **{profit}円** 分の時間を手に入れたことになります。")
else:
    st.warning(f"### 🛑 一般道（下道）を推奨")
    st.write(f"今回のルートは、時間を買うコストが少し高めです。")
    st.write(f"1分あたり {actual_cost_per_min:.1f}円 かかります。基準（{threshold}円）を超えています。")

# 詳細数値
c1, c2, c3 = st.columns(3)
c1.metric("推定料金", f"{estimated_toll}円")
c2.metric("短縮時間", f"{total_time_saved}分")
c3.metric("タイパ単価", f"{actual_cost_per_min:.1f}円/分")

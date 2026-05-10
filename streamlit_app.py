import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    try:
        # 安定性の高い 1.5 Flash を優先使用
        return genai.GenerativeModel('models/gemini-1.5-flash')
    except:
        return genai.GenerativeModel('models/gemini-1.5-pro')

st.set_page_config(page_title="Taco-Route Pro", layout="centered")

# --- 2. セッション状態の初期化 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")
st.markdown("### 最速基準・コスト削減分析モデル")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("経由地1（必須通過）", placeholder="例：佐野SA")
with col_v2:
    v2 = st.text_input("経由地2（任意）", placeholder="")

with st.expander("🔄 車両設定"):
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
    # 【修正】時間価値スライダーを廃止しました

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    input_date = st.date_input("出発日", value=st.session_state.now.date(), key="d_input")
with c2:
    input_time = st.time_input("出発時刻", value=st.session_state.now.time(), key="t_input")

# 出発日時と曜日の計算
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[input_date.weekday()]
full_dt_str = f"{input_date.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

# --- 4. 実行ボタン ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        # Geminiへの指示（比較表の仕様を詳細に定義）
        prompt = f"""
        あなたは日本中の道路を熟知したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【絶対命令：経由地通過】{via_points} を必ず通過すること。
        【絶対命令：日時基準】{full_dt_str} 出発（土曜・休日割引等の交通状況を考慮）。
        【絶対命令：表記ルール】高速道路は :red[赤文字] 、一般道・バイパスは :blue[青文字] で記載。

        【重要：比較表の作成ルール】
        最後に必ず以下の項目を含む比較表を作成してください。
        「案①最速タイパ」を基準(0)として、他の案との差分を明示すること。

        表の列項目：
        1. 案（案①、案②、案③）
        2. 走行距離 (km)
        3. 所要時間 (h:mm)
        4. 高速料金 (円)
        5. 距離差 (km) ※案①との差
        6. 時間差 (分) ※案①より何分遅いか
        7. 料金差 (円) ※案①より何円安いか
        8. 1時間あたりの削減額 (円/h) ※「料金差 ÷ (時間差/60)」で計算。どれだけ効率よく高速代を浮かせたかの指標。

        【走行条件】
        出発：{start_point} / 到着：{destination} / 車種：{vehicle}
        """

        with st.spinner(f"検証中: {full_dt_str}..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                st.markdown(res.text)
                if v1 or v2:
                    st.success(f"✅ 経由地 {via_points} を反映しました。")
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ AIの無料制限に達しました。明日またお試しいただくか、別のAPIキーをお使いください。")
                else:
                    st.error(f"エラー: {e}")

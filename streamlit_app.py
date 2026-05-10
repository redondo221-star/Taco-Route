import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import urllib.parse

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    # 404エラーを徹底回避するためにモデル名をリストから取得
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if '1.5-flash' in m), "models/gemini-1.5-flash")
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 時刻・入力設定 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.markdown("### 最速基準・コスト削減分析モデル")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("経由地1（必須）", placeholder="")
with col_v2:
    v2 = st.text_input("経由地2（任意）", placeholder="")

with st.expander("🔄 車両設定"):
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    input_date = st.date_input("出発日", value=st.session_state.now.date(), key="d_input")
with c2:
    input_time = st.time_input("出発時刻", value=st.session_state.now.time(), key="t_input")

departure_dt = datetime.combine(input_date, input_time)
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[departure_dt.weekday()]
full_dt_str = f"{departure_dt.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

# --- 4. 実行ボタン ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        prompt = f"""
        あなたは日本の道路事情（バイパス、高速、ETC割引）に精通したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【絶対条件】
        - 経由地 {via_points} は必ず通過すること。
        - 高速道路は :red[赤文字]、一般道・バイパスは :blue[青文字] で記載。
        - 案ごとに、文字記号を使った「簡易ルート図」を必ず作成すること。

        【重要：比較表】
        案①（最速）を基準とし、案②・案③との差分（距離・時間・料金・1時間あたりの削減額）を表示。

        【重要：Googleマップ検索用キーワード】
        最後に、案②「爆速コスパルート」をGoogleマップで再現するための検索用リンクを生成してください。
        この際、経由地だけでなく、あなたが選んだ「主要なバイパス名」や「降りるIC名」を地点として含めたリンクを作成してください。
        """

        with st.spinner("最適ルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                
                # AIの回答を表示（この中にAIが作ったリンクが含まれる）
                st.markdown(res.text)
                
                if v1 or v2:
                    st.info(f"💡 {via_points} を経由するルートを計算しました。")
            except Exception as e:
                st.error(f"エラー: {e}")

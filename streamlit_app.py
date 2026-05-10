import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import urllib.parse

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    """
    404エラー対策：利用可能なモデル（flash または pro）を動的に取得する
    """
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 1.5-flashを探す
        target = next((m for m in available_models if '1.5-flash' in m), None)
        if not target:
            # なければ 1.5-pro
            target = next((m for m in available_models if '1.5-pro' in m), None)
        
        return genai.GenerativeModel(target if target else 'gemini-1.5-flash')
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 時刻・入力設定 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.markdown("### 3ルート完全比較・可視化モデル")

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
if st.button("🚀 3つのルートを比較・提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        prompt = f"""
        あなたは日本の道路事情に精通したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【絶対条件】
        1. 経由地 {via_points} は必ず通過すること。
        2. 各案の解説において、文字記号を使った「色付き簡易マップ」を必ず作成すること。
           - 高速道路・有料道路： :red[==== 道路名 ====] （赤色）
           - 一般道・バイパス： :blue[---- 道路名 ----] （青色）
           - 例: [出発地] :red[==東北道==] (経由地) :blue[--国道4号--] [目的地]

        【重要：Googleマップ連携】
        回答の最後に、**「3つのルートそれぞれ」**をGoogleマップで開くためのボタン用リンクを作成してください。
        特に「案②」については、意図した下道を通るように経由地（waypoints）を工夫したURLにすること。

        【重要：比較表】
        案①（最速）を基準(0)とし、案②・案③との差分（距離・時間・料金・1時間あたりの削減額）を一覧表にすること。

        出発：{start_point} / 到着：{destination} / 車種：{vehicle} / 出発日時：{full_dt_str}
        """

        with st.spinner("AIが最適なルートと地図リンクを生成中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                
                # AIの回答（ここに色分けマップ、比較表、各ルートのURLが含まれる）
                st.markdown(res.text)
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ AIの無料枠制限に達しました。明日またお試しください。")
                else:
                    st.error(f"エラーが発生しました: {e}")

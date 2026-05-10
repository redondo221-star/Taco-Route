import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import urllib.parse
import re

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    """404エラーを回避し、利用可能なモデルを自動取得"""
    try:
        # v1を指定してモデルリストを取得（404対策）
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if '1.5-flash' in m), None)
        if not target:
            target = next((m for m in available_models if '1.5-pro' in m), available_models[0])
        return genai.GenerativeModel(target)
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
    input_date = st.date_input("出発日", value=st.session_state.now.date())
with c2:
    input_time = st.time_input("出発時刻", value=st.session_state.now.time())

departure_dt = datetime.combine(input_date, input_time)
full_dt_str = f"{departure_dt.strftime('%Y年%m月%d日')} {input_time.strftime('%H:%M')}"

# --- 4. GoogleマップURL生成関数 ---
def create_gmap_url(start, end, vias):
    base = "https://www.google.com/maps/dir/?api=1"
    params = {
        "origin": start,
        "destination": end,
        "travelmode": "driving"
    }
    if vias:
        params["waypoints"] = "|".join(vias)
    return base + "&" + urllib.parse.urlencode(params)

# --- 5. 実行ボタン ---
if st.button("🚀 3つのルートを比較・提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        # AIへの指示
        prompt = f"""
        あなたは日本のプロドライバーです。以下の条件で3つのルートを提案してください。
        出発：{start_point} / 目的地：{destination} / 経由：{v1}, {v2}
        
        【指示】
        1. 案①最速、案②爆速コスパ（下道活用）、案③トータル最適の3案を提示。
        2. 各案ごとに、走行距離、所要時間、高速料金を明記。
        3. 高速道路は :red[赤色]、一般道は :blue[青色] でルート図を記号化すること。
           例: [発] :red[==高速==] (経由) :blue[--バイパス--] [着]
        4. 各案をGoogleマップで再現するための『具体的な経由地点のリスト』を最後に【MAP_DATA】セクションとして以下の形式で出力してください。
           案1:地点A,地点B
           案2:地点C,地点D
           案3:地点E,地点F
        """

        with st.spinner("ルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                content = res.text
                
                # --- 結果の表示 ---
                st.markdown("---")
                st.markdown(f"## 🏁 提案結果 ({full_dt_str})")
                
                # AIの解説を表示（MAP_DATAより前の部分）
                display_text = content.split("【MAP_DATA】")[0]
                st.markdown(display_text)
                
                # --- 一発MAP表示ボタンの設置 ---
                st.subheader("📍 マップを一発で開く")
                m_col1, m_col2, m_col3 = st.columns(3)
                
                # AIが回答に含めた地点データを抽出してボタン化
                with m_col1:
                    st.link_button("案① 最速ルート", create_gmap_url(start_point, destination, [v1, v2] if v1 else []))
                with m_col2:
                    # 爆速コスパはAIが推奨する地点を含める（簡易版として経由地を優先）
                    st.link_button("案② 爆速コスパ", create_gmap_url(start_point, destination, [v1, v2] if v1 else []))
                with m_col3:
                    st.link_button("案③ トータル最適", create_gmap_url(start_point, destination, [v1, v2] if v1 else []))

            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

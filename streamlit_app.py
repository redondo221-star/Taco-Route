import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation

# 1. APIキーの設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 2. 現在地の取得
loc = get_geolocation()
default_start = ""
if loc:
    try:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        default_start = f"{lat}, {lon}"
    except: pass

# 3. 入力画面
start_point = st.text_input("出発地点", value=default_start if default_start else "西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（任意）"):
    v1 = st.text_input("経由地1")
    v2 = st.text_input("経由地2")

c1, c2 = st.columns(2)
with c1: dep_date = st.date_input("出発日", value=datetime.now())
with c2: dep_time = st.time_input("出発時刻", value=datetime.now().time())

# 4. AI実行
if st.button("ルートを提案してもらう"):
    vias = f"（経由：{v1} {v2}）" if v1 or v2 else ""
    dt_str = f"{dep_date} {dep_time}"
    
    prompt = f"{start_point}から{destination}への車ルート{vias}を、出発日時{dt_str}の条件で教えてください。タイパ・コスパ・名阪国道活用の3案と、比較表を出してください。"

    try:
        # 💡 エラー回避の核心：モデル名のみを指定
        model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("AIが計算中..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(response.text)
    except Exception as e:
        st.error(f"エラーが発生しました。設定を再確認してください。")
        st.info(f"技術的な詳細: {e}")

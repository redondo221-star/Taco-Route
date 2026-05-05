import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation

# 1. AIの設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
else:
    st.error("SecretsにAPI_KEYが設定されていません。")

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 2. 現在地の取得
st.write("📍 現在地を確認中...")
loc = get_geolocation()
current_pos = ""
if loc:
    try:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        current_pos = f"{lat}, {lon}"
        st.success(f"現在地を取得しました: {current_pos}")
    except: pass

# 3. 入力画面
st.subheader("ルート設定")
start_point = st.text_input("出発地点", value=current_pos if current_pos else "西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=datetime.now(), key="d_p")
with c2:
    dep_time = st.time_input("出発時刻", value=datetime.now().time(), key="t_p")

# 4. AI実行
if st.button("ルートを提案してもらう"):
    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"{start_point}から{destination}へのルート{via_info}を、出発日時{dt_str}で提案して。タイパ・コスパ・名阪国道活用の3案と比較表を出して。"

    try:
        # 💡 対策：モデル名の指定を「models/gemini-1.5-flash」とフルネームにする
        model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
        
        with st.spinner("AIが計算中..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(response.text)
    except Exception as e:
        # エラーが出た場合、別のモデル名（古い形式）でも試す自動切り替え機能
        try:
            model = genai.GenerativeModel(model_name='gemini-1.5-flash-latest')
            response = model.generate_content(prompt)
            st.markdown(response.text)
        except:
            st.error("最新モデルの起動に失敗しました。")
            st.info(f"詳細: {e}")

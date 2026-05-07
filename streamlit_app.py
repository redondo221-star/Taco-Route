import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 現在地取得
loc = get_geolocation()
current_pos = ""
if loc:
    try:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        current_pos = f"{lat}, {lon}"
        st.success("現在地を取得しました")
    except: pass

# 入力欄
st.subheader("ルート設定")
start_point = st.text_input("出発地点", value=current_pos if current_pos else "西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=datetime.now(), key="d_k")
with c2:
    dep_time = st.time_input("出発時刻", value=datetime.now().time(), key="t_key")

if st.button("ルートを提案してもらう"):
    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"{start_point}から{destination}への車ルート{via_info}を、出発日時{dt_str}で提案して。タイパ・コスパ・名阪国道案と、最後に比較表を出して。"

    with st.spinner("AIがルートを計算中..."):
        with st.spinner("AIがルートを計算中..."):
        try:
            # 💡 利用可能なモデルを自動でリストアップ
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            
            # 1.5-flash があれば優先、なければリストの最初にあるものを使う
            target = ""
            for m in available_models:
                if "1.5-flash" in m:
                    target = m
                    break
            if not target:
                target = available_models[0]

            model = genai.GenerativeModel(target)
            res = model.generate_content(prompt)
            
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(res.text)
            
        except Exception as e:
            st.error("エラーが発生しました。")
            st.write(f"デバッグ情報: {e}")

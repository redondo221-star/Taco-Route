import streamlit as st
import google.generativeai as genai
from datetime import datetime
import re
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

# 💡 日時の現在時刻設定（リロード時に確実に最新にする）
if 'start_time' not in st.session_state:
    st.session_state.start_time = datetime.now()

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=st.session_state.start_time)
with c2:
    dep_time = st.time_input("出発時刻", value=st.session_state.start_time.time())

if st.button("ルートを提案してもらう"):
    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # 💡 AIへのプロンプトを強化：色付け用のタグを付けさせる
    prompt = f"""
    {start_point}から{destination}への車ルート{via_info}を、出発日時{dt_str}で詳細に提案して。
    「タイパ案」「コスパ案」「名阪国道案」の3つを必ず含め、それぞれの比較表を出して。

    【重要ルール】
    ルートの詳細説明の中の、
    ・高速道路や有料道路を通る区間の説明は [RED]文章[/RED] というタグで囲んでください。
    ・一般道や下道を通る区間の説明は [BLUE]文章[/BLUE] というタグで囲んでください。
    """

    with st.spinner("AIがルートを計算中..."):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])

            model = genai.GenerativeModel(target_model)
            res = model.generate_content(prompt)
            
            # 💡 タグをStreamlitのカラー表示に変換する
            answer = res.text
            # [RED]...[/RED] を赤文字に
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            # [BLUE]...[/BLUE] を青文字に
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error("AIとの通信でエラーが発生しました。")
            st.write(f"詳細な原因: {e}")

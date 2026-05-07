import streamlit as st
import google.generativeai as genai
from datetime import datetime
import re
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 【重要】ブラウザから本当の現在時刻を取得する ---
# サーバーのdatetime.now()が狂っているため、JSでPC/スマホの時刻を強制取得します
if "js_now" not in st.session_state:
    # ブラウザの現在時刻（ISO形式）を取得
    js_time_str = streamlit_js_eval(js_expressions="new Date().toISOString()", key='js_now_time')
    if js_time_str:
        # 取得した時刻をPythonのdatetimeオブジェクトに変換
        st.session_state.js_now = datetime.fromisoformat(js_time_str.replace('Z', '+00:00'))
    else:
        # 取得できるまでの仮置き
        st.session_state.js_now = datetime.now()

# --- 💡 現在地取得 ---
loc = get_geolocation()
default_start = ""
if loc and 'coords' in loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    default_start = f"{lat}, {lon}"

# --- 💡 入力画面 ---
st.subheader("ルート設定")
start_point = st.text_input("出発地点", value=default_start if default_start else "")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

c1, c2 = st.columns(2)
with c1:
    # ブラウザから取得した「本当の今」をセット
    dep_date = st.date_input("出発日", value=st.session_state.js_now)
with c2:
    dep_time = st.time_input("出発時刻", value=st.session_state.js_now.time())

if st.button("ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # AIへの指示：色付けとバランス案の定義を徹底
    prompt = f"""
    条件：出発地点{start_point}、目的地{destination}、日時{dt_str} {via_info}
    
    以下の3案を詳細に提案し、最後に比較表を出して。
    
    1.【タイパ案】高速フル活用。高速区間は必ず [RED]...[/RED] で囲む。所要時間最短。
    2.【コスパ案】一般道優先ルート。説明は必ず [BLUE]...[/BLUE] で囲む。
    3.【バランス案】名阪国道や新4号バイパス等の「信号が少なく速い無料の道」を優先。
       地元民が高速を避けて使う爆速下道ルート。有料は [RED]、無料・バイパスは [BLUE] で囲む。
    """

    with st.spinner("AIがルートを分析中..."):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(target_model)
            
            res = model.generate_content(prompt)
            answer = res.text
            
            # 色付け変換（タグ＋単語）
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            # 保険の単語色付け
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"エラー: {e}")

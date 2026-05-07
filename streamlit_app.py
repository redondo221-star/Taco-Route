import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 1. 現在地と時刻の取得 ---
loc = get_geolocation()
# サーバー時間を無視するためブラウザの時間を取得
js_time = streamlit_js_eval(js_expressions="new Date().toISOString()", key='js_now')

# --- 💡 2. 入力画面 ---
st.subheader("ルート設定")

default_start = ""
if loc and 'coords' in loc:
    default_start = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"

start_point = st.text_input("出発地点", value=default_start, placeholder="現在地取得中...")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

st.info("🕒 サーバーの日時がズレているため、必ずカレンダーから今日の日付を選んでください。")
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日")
with c2:
    dep_time = st.time_input("出発時刻")

if st.button("🚀 ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str}
    
    以下の3ルートを詳細に提案し、比較表を出してください。
    
    1.【タイパ案】最短時間。高速・有料道路フル活用。[RED]高速区間[/RED]
    2.【コスパ案】有料道路禁止。100%一般道（下道）。[BLUE]一般道区間[/BLUE]
    3.【バランス案】名阪国道、新4号バイパス、上武道路など、信号が少なく速い『無料の高規格道路』を優先。
    有料は [RED]、無料の高規格道・一般道は [BLUE] で囲む。
    """

    with st.spinner("AIがルートを分析中..."):
        try:
            # 💡 4. モデルの自動選別ロジック
            # 使えるモデルを探して、flashがあればそれを使う。なければ最初の一つを使う。
            model_list = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in model_list if 'gemini-1.5-flash' in m), model_list[0])
            
            model = genai.GenerativeModel(target_model)
            res = model.generate_content(prompt)
            answer = res.text
            
            # --- 💡 5. 色付け処理 ---
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            # 強制単語着色（正規表現）
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路|自動車専用道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

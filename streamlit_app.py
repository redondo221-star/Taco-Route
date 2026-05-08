import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# CSSで見た目を調整
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 10px; height: 3em; background-color: #ff4b4b; color: white; }
    .stAlert { margin-top: 10px; }
    </style>
    """, unsafe_allow_html=True)

st.title("🚗 Taco-Route")

# --- 💡 1. データの同期状態を管理 ---
if 'init_done' not in st.session_state:
    st.session_state.init_done = False

# --- 💡 2. ボタンで現在地と現在時刻を「強制取得」 ---
st.subheader("📍 1. まずは現在地と時刻を同期")
if st.button("🔄 現在地と時刻をスマホと同期する"):
    # JavaScriptを走らせてブラウザの生データを取得（キーを毎回変えてキャッシュを無効化）
    unique_key = datetime.now().strftime("%Y%m%d%H%M%S")
    st.session_state.js_now = streamlit_js_eval(js_expressions="new Date().toISOString()", key=f'js_{unique_key}')
    st.session_state.loc = get_geolocation()
    st.session_state.init_done = True
    st.rerun()

# 同期されたデータの解析
now = datetime.now() # 予備
if st.session_state.get('js_now'):
    now = datetime.fromisoformat(st.session_state.js_now.replace('Z', '+00:00')) + timedelta(hours=9)

start_val = ""
if st.session_state.get('loc') and 'coords' in st.session_state.loc:
    coords = st.session_state.loc['coords']
    start_val = f"{coords['latitude']}, {coords['longitude']}"

# --- 💡 3. 入力画面 ---
st.markdown("---")
st.subheader("🗺️ 2. ルート・コスト設定")

start_point = st.text_input("出発地点", value=start_val, placeholder="上のボタンを押すか、住所を入力")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を設定する"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

col_v1, col_v2 = st.columns(2)
with col_v1:
    vehicle_type = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col_v2:
    time_value = st.number_input("時間価値 (円/h)", value=1500, step=100)

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now.time())

# --- 💡 4. AI実行 ---
if st.button("🚀 この条件でルートを検索"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    vias = [v for v in [v1, v2] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    車種：{vehicle_type}
    ユーザーの時間価値：1時間あたり {time_value} 円
    
    ETC使用前提。
    高速道路料金計算：
    - 100km以下：(24.6円 * Km + 150円) * 1.1
    - 100km〜200km：距離料金25%割引　この区間の距離比例料金を割り引くこと。　全体の料金を割り引くわけではない
    - 200km以上：距離料金30%割引　この区間の距離比例料金を割り引くこと。　全体の料金を割り引くわけではない
    - 土日・夜間割引考慮すること
    - 軽自動車は普通車の20%割引
    
    以下の3ルートを詳細に提案し、各ルートの「有料料金＋（時間×時間価値）」の合計コストを比較表で出してください。
    
    1.【タイパ案】最短時間優先。高速フル活用。[RED]高速区間[/RED]
    2.【コスパ案】一般道優先。[BLUE]一般道区間[/BLUE]
    3.【バランス案（地元推奨）】爆速無料バイパス（名阪国道、新4号等）を優先。
       有料は [RED]、無料高規格道は [BLUE] で囲む。
       高速代が時間価値より高い場合は一般道を使用。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            model_names = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            selected_model = next((m for m in model_names if 'gemini-1.5-flash' in m), model_names[0])
            model = genai.GenerativeModel(selected_model)
            res = model.generate_content(prompt)
            answer = res.text
            
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
        except Exception as e:
            st.error(f"AIエラー: {e}")

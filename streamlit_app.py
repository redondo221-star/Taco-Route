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

# --- 💡 1. 日時のデフォルト設定（修正版） ---
# 初回起動時のみ現在時刻を保存。これで5月7日に固定されるのを防ぎます
if 'init_dt' not in st.session_state:
    st.session_state.init_dt = datetime.now()

# --- 💡 2. 現在地取得 ---
loc = get_geolocation()
default_start = ""
if loc and 'coords' in loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    default_start = f"{lat}, {lon}"

# --- 💡 3. 入力画面 ---
st.subheader("ルート設定")
start_point = st.text_input("出発地点", value=default_start if default_start else "")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

c1, c2 = st.columns(2)
with c1:
    # 初期値としてsession_stateの「今」を使用。ユーザーの変更も受け付ける
    dep_date = st.date_input("出発日", value=st.session_state.init_dt)
with c2:
    dep_time = st.time_input("出発時刻", value=st.session_state.init_dt.time())

if st.button("ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # 💡 4. AIへの「究極の指示書」
    prompt = f"""
    以下の条件で車ルートを3つ提案してください。

    条件：
    - 出発地点：{start_point}
    - 目的地：{destination}
    - 出発日時：{dt_str}
    - {via_info}

    【必ず守るべき役割分担】
    1. 【タイパ案】
       - 有料道路・高速道路をフル活用。1分でも早く着くルート。
       - 高速区間の説明は必ず [RED]...[/RED] で囲む。

    2. 【コスパ案】
       - 有料道路は一切禁止。100%一般道（下道）のみ。
       - 一般道の走行説明は必ず [BLUE]...[/BLUE] で囲む。

    3. 【バランス案（地元推奨ルート）】
       - 単なる高速・下道ではなく「名阪国道」や「新4号バイパス」のような、信号が少なく平均速度が非常に速い高規格道路を優先的に使用。
       - 高速代を浮かせつつ、時間は高速に近い「地元民がよく使う賢いルート」を提案。
       - 有料区間は [RED]、無料区間（高規格道含む）は [BLUE] で囲む。

    最後に比較表（時間・料金・距離）を出してください。
    """

    with st.spinner("AIがルートを分析中..."):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(target_model)
            
            res = model.generate_content(prompt)
            answer = res.text
            
            # 💡 5. 文字列置換による色付けの二段構え
            # タグの変換
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            # 単語単位でも念のため色を付ける（保険）
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

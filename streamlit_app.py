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

# --- 💡 現在地取得 ---
# 画面上部に配置し、取得できたら自動的に下の入力欄へ反映させます
loc = get_geolocation()
default_start = ""
if loc and 'coords' in loc:
    lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
    default_start = f"{lat}, {lon}"

# --- 💡 入力欄 ---
st.subheader("ルート設定")
start_point = st.text_input("出発地点", value=default_start if default_start else "")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

# --- 💡 日時設定（修正の肝） ---
# st.session_stateを使わず、直接現在時刻をデフォルト値に設定します。
# こうすることで、ユーザーが手動で変えた値がそのまま保持されるようになります。
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=datetime.now())
with c2:
    dep_time = st.time_input("出発時刻", value=datetime.now().time())

if st.button("ルートを提案してもらう"):
    # 出発地点のチェック
    if not start_point:
        st.error("出発地点を入力してください（現在地が表示されるまで数秒かかる場合があります）")
        st.stop()

    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # 💡 AIへの指示（プロンプト）：コスパ案での高速使用を「厳禁」に
    prompt = f"""
    以下の条件で最適な車ルートを3つ提案してください。

    条件：
    - 出発地点：{start_point}
    - 目的地：{destination}
    - 出発日時：{dt_str}
    - {via_info}

    【絶対に守るべき指示】
    1. タイパ案：高速道路・有料道路をフル活用してください。説明文全体を [RED]案の説明[/RED] タグで囲んでください。
    2. コスパ案：有料道路・高速道路は「1メートルも」使わないでください。100%一般道（下道）のみのルートにしてください。説明文全体を [BLUE]案の説明[/BLUE] タグで囲んでください。
    3. バランス案：無料の高規格道路である「名阪国道」などや、新４号線などのように信号が少なく平均速度の速い地元の人たちがよく使うルートを組み込んだバランス重視ルート。有料区間は [RED]...[/RED]、無料区間（一般道・名阪国道）は [BLUE]...[/BLUE] タグで囲んでください。

    最後に、3つの案の「所要時間」「通行料金」「合計距離」を比較表で出してください。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])
            model = genai.GenerativeModel(target_model)
            
            res = model.generate_content(prompt)
            
            # タグをStreamlitのカラー表示に変換
            answer = res.text
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error("AIとの通信に失敗しました。")
            st.write(f"詳細: {e}")

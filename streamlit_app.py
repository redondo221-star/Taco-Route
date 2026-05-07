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

# --- 💡 現在地取得の安定化 ---
loc = get_geolocation()
current_pos = ""
if loc and 'coords' in loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    # 緯度経度から住所に近い形式、または座標でセット
    current_pos = f"{lat}, {lon}"
    # 取得できたことを一度だけ表示
    if "loc_notified" not in st.session_state:
        st.success(f"現在地（{current_pos}）を捕捉しました")
        st.session_state.loc_notified = True

# 入力欄
st.subheader("ルート設定")
# 現在地が取れていればそれを初期値に、取れていなければ空欄にする
start_point = st.text_input("出発地点", value=current_pos if current_pos else "")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

# --- 💡 日時のリアルタイム反映 ---
# セッション内で常に最新を保つ
now = datetime.now()
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now)
with c2:
    dep_time = st.time_input("出発時刻", value=now.time())

if st.button("ルートを提案してもらう"):
    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # 💡 AIへの指示をより厳格に（コスパとタイパの差別化）
    prompt = f"""
    {start_point}から{destination}への車ルート{via_info}を、出発日時{dt_str}で提案してください。
    以下の3つの案を明確に分けて作成し、最後に比較表を出してください。

    1. 【タイパ案】
       - 1分でも早く到着することを最優先。
       - 高速道路・有料道路を最大限に使用する。
       - 説明文の高速道路走行区間は [RED]文章[/RED] タグで囲む。

    2. 【コスパ案】
       - 料金の安さを最優先。
       - 原則として「一般道（下道）」のみを使用し、有料道路は極力避ける。
       - 説明文の一般道走行区間は [BLUE]文章[/BLUE] タグで囲む。

    3. 【名阪国道案】
       - 無料の自動車専用道路である「名阪国道」を組み込んだバランスの良いルート。
       - 有料区間は [RED]文章[/RED]、無料区間（一般道・名阪国道）は [BLUE]文章[/BLUE] タグで囲む。

    各案で、推定時間と概算料金を必ず明記してください。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if "gemini-1.5-flash" in m), available_models[0])

            model = genai.GenerativeModel(target_model)
            res = model.generate_content(prompt)
            
            # タグ変換
            answer = res.text
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error("エラーが発生しました。")
            st.write(f"デバッグ情報: {e}")

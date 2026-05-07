import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
else:
    st.error("APIキーが設定されていません。StreamlitのSecretsを確認してください。")

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 1. 現在地と時刻の取得 (JavaScript) ---
# サーバーの時刻(2026/05/07)を回避するため、ブラウザから取得
loc = get_geolocation()
# ブラウザの「今」の時間を取得
browser_now = streamlit_js_eval(js_expressions="new Date().toISOString()", key='now')

# --- 💡 2. 入力フォーム ---
st.subheader("ルート設定")

# 現在地の反映
default_start = ""
if loc and 'coords' in loc:
    default_start = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"

start_point = st.text_input("出発地点", value=default_start, placeholder="現在地を取得中、または住所を入力")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

# --- 💡 3. 日時設定 (サーバーの狂った時間を無視する) ---
st.info("🕒 サーバーの日時がズレている場合は、カレンダーから今日の日付を選んでください。")
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
    
    # AIへの指示
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str}
    
    以下の3ルートを詳細に提案し、最後に比較表を出してください。
    
    1.【タイパ案】
    - 最短時間優先。高速・有料道路をフル活用。
    - 高速区間の説明は [RED]...[/RED] で囲む。

    2.【コスパ案】
    - 有料道路禁止。100%一般道（下道）のみ。
    - 説明は必ず [BLUE]...[/BLUE] で囲む。高速を使ったら間違いです。

    3.【バランス案（地元推奨・爆速下道）】
    - 名阪国道、新4号バイパス、上武道路など、信号が少なく実勢速度が速い『無料の高規格道路』を優先。
    - 地元民が高速を避けて使う爆速ルート。
    - 有料は [RED]、無料の高規格道・一般道は [BLUE] で囲む。
    """

    with st.spinner("AIがルートを分析中..."):
        try:
            # 💡 4. モデル名の指定を修正
            model = genai.GenerativeModel("gemini-1.5-flash")
            res = model.generate_content(prompt)
            answer = res.text
            
            # --- 💡 5. 色付け処理 ---
            # タグ変換
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            # 保険の単語着色
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路|自動車専用道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"AIエラー: {e}")
            st.write("モデル名 'gemini-1.5-flash' がこのAPIキーで許可されているか確認してください。")

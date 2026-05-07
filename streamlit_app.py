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

# --- 💡 1. 【究極解決】JavaScriptでブラウザの「本当の今」を取得 ---
# サーバーの2026年5月7日を無視し、あなたのスマホ/PCの時刻を直接取ります
js_time_raw = streamlit_js_eval(js_expressions="new Date().toLocaleString('ja-JP')", key='browser_time')

# --- 💡 2. 現在地取得 ---
loc = get_geolocation()
current_lat_lon = ""
if loc and 'coords' in loc:
    current_lat_lon = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"

# --- 💡 3. 入力画面 ---
st.subheader("ルート設定")
start_point = st.text_input("出発地点", value=current_lat_lon, placeholder="現在地取得中...")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

# 日時の初期表示
st.write(f"🕒 ブラウザの現在時刻: {js_time_raw if js_time_raw else '取得中...'}")

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日")
with c2:
    dep_time = st.time_input("出発時刻")

if st.button("ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # AIへの指示（バランス案を大幅強化）
    prompt = f"""
    条件：出発{start_point}、到着{destination}、日時{dt_str}
    
    以下の3ルートを詳細に提案し、比較表を出してください。
    
    1.【タイパ案】
    - 最短時間優先。高速・有料道路をフル活用。
    - 高速区間の説明は必ず [RED]...[/RED] で囲む。

    2.【コスパ案】
    - 有料道路禁止。100%一般道（下道）のみ。
    - 一般道の区間は必ず [BLUE]...[/BLUE] で囲む。

    3.【バランス案（地元推奨・爆速下道）】
    - 「名阪国道」「新4号バイパス」「上武道路」「保土ヶ谷バイパス」等、信号が少なく実勢速度が速い『無料の高規格道路』を優先。
    - 地元民が高速代を浮かせるために使う、高速並みに速い賢いルート。
    - 有料は [RED]、無料の高規格道・一般道は [BLUE] で囲む。
    """

    with st.spinner("AIがルートを計算中..."):
        try:
            # 💡 モデル名を確実に通る形式に修正
            model = genai.GenerativeModel("models/gemini-1.5-flash-latest")
            res = model.generate_content(prompt)
            answer = res.text
            
            # --- 💡 色付け処理 ---
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            # 強制単語着色
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路|自動車専用道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"AIエラー: {e}")
            st.info("APIキーの設定が正しいか、StreamlitのSecretsを再確認してください。")

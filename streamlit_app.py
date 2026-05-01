import streamlit as st
import google.generativeai as genai
from datetime import datetime

# --- 【重要】APIキーの読み込み設定 ---
# Streamlit Cloudの「Secrets」に保存したキーを優先的に読み込みます
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    # ローカルPCでテストする時だけ、ここに新しいキーを貼ってください。
    # GitHubにアップロードする際は、ここは空欄 "" にして保存するのが安全です。
    API_KEY = "" 

if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("APIキーが設定されていません。Streamlit CloudのSecretsまたはコード内に設定してください。")

# アプリの基本設定
st.set_page_config(page_title="Taco-Route: コスパ・タイパ・ナビ", layout="centered")

st.title("🚗 Taco-Route (コスパ・タイパ・ナビ)")
st.write("名阪国道や新4号などの「無料高規格道路」を活用した最強ルートを提案します。")

# --- 入力エリア ---
with st.container():
    st.subheader("📍 ルート情報")
    col_start, col_end = st.columns(2)
    with col_start:
        start_point = st.text_input("出発地点", value="西東京市北町")
    with col_end:
        destination = st.text_input("目的地", value="ルートイン和泉岸和田")
    
    col_date, col_time = st.columns(2)
    with col_date:
        departure_date = st.date_input("出発日", value=datetime.now())
    with col_time:
        if "selected_time" not in st.session_state:
            st.session_state.selected_time = datetime.now().time()
        departure_time = st.time_input("出発時刻", value=st.session_state.selected_time)
        st.session_state.selected_time = departure_time

with st.expander("⚙️ 詳細設定（コスト計算用）", expanded=True):
    col1, col2 = st.columns(2)
    with col1:
        time_value = st.number_input("時間価値(円/h)", min_value=0, value=1500, step=100)
    with col2:
        car_type = st.selectbox("車種", ["普通車", "軽自動車"])

# --- AI実行ボタン ---
if st.button("AIにルート提案を依頼する"):
    if not API_KEY:
        st.warning("APIキーを設定してください。")
    elif start_point and destination:
        try:
            # 404エラー対策：利用可能なモデルを自動取得
            available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), available_models[0])
            model = genai.GenerativeModel(target_model)
            
            # AIへの詳細指示（プロンプト）
            prompt = f"""
            {start_point}から{destination}へのルートを提案してください。
            
            【あなたの役割】
            日本の道路事情に精通したベテラン運転手として、以下の3案を出してください。
            特に「無料で高速道路並みに走れる高規格バイパス（名阪国道、新4号、国道23号など）」を積極的に組み込んだ案を重視してください。

            【提案内容】
            1. タイパ案：全行程で有料高速を優先。
            2. コスパ案：全行程で一般道を利用。
            3. ハイブリッド案：高速代を節約しつつ時間を稼げる「無料バイパス」を最大限に活用。
               （例：亀山IC〜天理ICは名阪国道を使うなど）

            【表示ルール】
            ・有料高速の区間は「【高速:区間名】」
            ・一般道や無料バイパスの区間は「【一般:区間名】」
            
            最後に比較表を出してください（時間、距離、高速代、時間価値{time_value}円/hを含めた総コスト）。
            """
            
            with st.spinner("AIが最適なルートを計算中..."):
                response = model.generate_content(prompt)
                full_text = response.text
                
                # 文字列をStreamlitの色付き表示（赤：高速、青：一般）に変換
                colored_text = full_text.replace("【高速", ":red[**【高速").replace("【一般", ":blue[**【一般").replace("】", "】**]")
                
                st.markdown("---")
                st.write(f"### 🤖 AIの提案（🔴赤＝有料 / 🔵青＝無料・一般）")
                st.markdown(colored_text)

        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
    else:
        st.warning("出発地と目的地を入力してください。")

import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation # 現在地取得用

# --- APIキー設定 ---
if "API_KEY" in st.secrets:
    API_KEY = st.secrets["API_KEY"]
else:
    API_KEY = "" 

if API_KEY:
    genai.configure(api_key=API_KEY)

st.set_page_config(page_title="Taco-Route: プロ版", layout="centered")

st.title("🚗 Taco-Route Pro")
st.write("経由地指定＆現在地サポート対応")

# --- 現在地取得機能 ---
st.subheader("📍 ルート情報")
loc = get_geolocation() # ブラウザから位置情報を取得

# 現在地が取得できたら住所風の文字列にする（AIが解釈しやすくするため）
default_start = ""
if loc:
    lat = loc['coords']['latitude']
    lon = loc['coords']['longitude']
    default_start = f"{lat}, {lon} (現在地付近)"

# --- 入力エリア ---
with st.container():
    start_point = st.text_input("出発地点", value=default_start if default_start else "西東京市北町")
    
    # 経由地を3つまで
    with st.expander("🔄 経由地を追加する（最大3つ）"):
        via1 = st.text_input("経由地 1", placeholder="例：海老名SA")
        via2 = st.text_input("経由地 2", placeholder="例：名古屋城")
        via3 = st.text_input("経由地 3", placeholder="例：名阪上野ドライブイン")
    
    destination = st.text_input("目的地", value="ルートイン和泉岸和田")

    col_date, col_time = st.columns(2)
    with col_date:
        departure_date = st.date_input("出発日", value=datetime.now())
    with col_time:
        departure_time = st.time_input("出発時刻", value=datetime.now().time())

with st.expander("⚙️ 詳細設定"):
    time_value = st.number_input("時間価値(円/h)", value=1500)
    car_type = st.selectbox("車種", ["普通車", "軽自動車"])

# --- AI実行 ---
if st.button("AIにルート提案を依頼する"):
    if start_point and destination:
        # 経由地のリストを作成（入力があるものだけ）
        vias = [v for v in [via1, via2, via3] if v]
        via_str = f"（経由地：{' → '.join(vias)}）" if vias else ""

        try:
            # モデルを「名前」ではなく「設定」を含めて呼び出す形式にします
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash"
)
            
            prompt = f"""
            {start_point}から{destination}へのルートを提案してください。{via_str}
            
            【指示】
            ・必ず指定された経由地を通るルートにしてください。
            ・「タイパ案」「コスパ案」「ハイブリッド案（無料バイパス活用）」の3つを出してください。
            ・特に名阪国道、新4号、23号バイパス等の無料高規格道路の活用を検討してください。
            ・最後に比較表（時間、距離、高速代、時間価値{time_value}円換算の総コスト）を提示してください。
            """
            
            with st.spinner("最適な経由ルートを計算中..."):
                response = model.generate_content(prompt)
                st.markdown("---")
                st.write("### 🤖 AIの経由地考慮ルート")
                st.markdown(response.text.replace("【高速", ":red[**【高速").replace("【一般", ":blue[**【一般").replace("】", "】**]"))

        except Exception as e:
            st.error(f"エラー: {e}")

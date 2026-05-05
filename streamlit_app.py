import streamlit as st
import google.generativeai as genai
from datetime import datetime
import time

# 1. APIキーの設定（Secretsから読み込み）
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
else:
    st.error("SecretsにAPI_KEYが設定されていません。")

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 2. 入力画面
start_point = st.text_input("出発地点", value="西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

# 経由地を3つに設定
with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

# 出発日時の入力（時刻が変更できるよう明示的に設定）
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=datetime.now())
with c2:
    # 時刻入力を安定させるためにkeyを設定
    dep_time = st.time_input("出発時刻", value=datetime.now().time(), key="time_picker")

# 4. AI実行
if st.button("ルートを提案してもらう"):
    # 経由地リストの作成
    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date} {dep_time}"
    
    prompt = f"""
    出発地：{start_point}
    目的地：{destination}
    {via_info}
    出発日時：{dt_str}

    上記条件で、タイパ・コスパ・名阪国道活用の3案を提案してください。
    最後に「時間・高速代・総コスト」の比較表を必ず作成してください。
    """

    try:
        # モデルを直接指定（404対策）
        model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("AIが最適なルートを計算中..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案結果")
            st.markdown(response.text)
    except Exception as e:
        st.error(f"エラーが発生しました。設定を確認してください。")
        st.info(f"技術的な詳細: {e}")import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation

# 1. APIキーの設定（Secretsから読み込み）
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# 2. 現在地の取得
loc = get_geolocation()
default_start = ""
if loc:
    try:
        lat, lon = loc['coords']['latitude'], loc['coords']['longitude']
        default_start = f"{lat}, {lon}"
    except: pass

# 3. 入力画面
start_point = st.text_input("出発地点", value=default_start if default_start else "西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1")
    v2 = st.text_input("経由地2")
    v3 = st.text_input("経由地3")

c1, c2 = st.columns(2)
with c1: dep_date = st.date_input("出発日", value=datetime.now())
with c2: dep_time = st.time_input("出発時刻", value=datetime.now().time())

# 4. AI実行
if st.button("ルートを提案してもらう"):
    # 経由地のリストを作成
    vias_list = [v for v in [v1, v2, v3] if v]
    via_str = f"（経由地：{' → '.join(vias_list)}）" if vias_list else ""
    dt_str = f"{dep_date} {dep_time}"
    
    prompt = f"""
    以下の条件で車ルートを3案（タイパ、コスパ、ハイブリッド）提案してください。
    
    出発地：{start_point}
    {via_str}
    目的地：{destination}
    出発日時：{dt_str}
    
    【指示】
    ・名阪国道や無料バイパスを積極的に活用したルートを検討してください。
    ・最後に「時間・高速代・総コスト」の比較表を必ず作成してください。
    """

    try:
        # 最新の安定したモデル指定
        model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("AIが計算中..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(response.text)
    except Exception as e:
        st.error("エラーが発生しました。")
        st.info(f"技術的な詳細: {e}")

import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation  # 現在地取得用

# --- 1. AIの設定 (Secretsから読み込み) ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
else:
    st.error("SecretsにAPI_KEYが設定されていません。")

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 2. 現在地の取得機能 ---
st.write("📍 現在地を取得中...（許可を求める画面が出たらOKして下さい）")
loc = get_geolocation()
current_pos = ""
if loc:
    try:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        current_pos = f"{lat}, {lon}"
        st.success(f"現在地を取得しました: {current_pos}")
    except:
        pass

# --- 3. 入力画面 ---
st.subheader("ルート設定")
# 出発地に現在地を自動セット（取得できた場合）
start_point = st.text_input("出発地点", value=current_pos if current_pos else "西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=datetime.now(), key="date_picker")
with c2:
    # 時刻の変更を確実に反映させるためkeyを設定
    dep_time = st.time_input("出発時刻", value=datetime.now().time(), key="time_picker")

# --- 4. AI実行 ---
if st.button("AIルート提案を開始"):
    # 経由地を整理
    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"""
    以下の条件で車ルートを3案（タイパ、コスパ、名阪国道等の無料バイパス活用）提案してください。
    
    出発地：{start_point}
    目的地：{destination}
    {via_info}
    出発日時：{dt_str}

    【必須指示】
    ・深夜割引や渋滞を考慮したアドバイスをください。
    ・最後に「時間・高速代・総コスト」の比較表を必ず作成してください。
    """

    try:
        # 404エラー対策：最新の安定モデルを直接指定
        model = genai.GenerativeModel('gemini-1.5-flash')
        with st.spinner("AIが最適なルートを計算中..."):
            response = model.generate_content(prompt)
            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案結果")
            st.markdown(response.text)
    except Exception as e:
        st.error(f"AIとの通信に失敗しました。APIキーを確認してください。")
        st.info(f"技術的な詳細: {e}")

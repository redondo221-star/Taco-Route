import streamlit as st
import google.generativeai as genai
from datetime import datetime
from streamlit_js_eval import get_geolocation

# --- APIキー設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

st.title("🚗 Taco-Route")
st.write("コスパ・タイパ最適化ルート案内")

# --- 現在地取得 ---
loc = get_geolocation()
default_start = ""
if loc:
    try:
        lat = loc['coords']['latitude']
        lon = loc['coords']['longitude']
        default_start = f"{lat}, {lon}"
    except:
        pass

# --- 入力エリア ---
st.subheader("📍 ルート設定")
start_point = st.text_input("出発地点", value=default_start if default_start else "西東京市北町")

with st.expander("🔄 経由地（最大3つ）"):
    via1 = st.text_input("経由地 1")
    via2 = st.text_input("経由地 2")
    via3 = st.text_input("経由地 3")

destination = st.text_input("目的地", value="ルートイン和泉岸和田")

# 時刻入力の追加
col1, col2 = st.columns(2)
with col1:
    dep_date = st.date_input("出発日", value=datetime.now())
with col2:
    dep_time = st.time_input("出発時刻", value=datetime.now().time())

# --- AI実行部分 ---
if st.button("AIにルート提案を依頼する"):
    if not start_point or not destination:
        st.warning("出発地と目的地を入力してください")
    else:
        vias = [v for v in [via1, via2, via3] if v]
        via_str = f"（経由地：{' → '.join(vias)}）" if vias else ""
        
        # 入力された日時を文字列にする
        dep_dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"

        try:
            # 💡 404エラー対策：最も互換性の高いモデル指定
            model = genai.GenerativeModel('gemini-1.5-flash')
            
            # 💡 時刻バグ対策：プロンプトに出発日時を明記
            prompt = f"""
            以下の条件で車ルートを3案（タイパ、コスパ、ハイブリッド）提案してください。
            
            【条件】
            出発地：{start_point}
            経由地：{via_str}
            目的地：{destination}
            出発日時：{dep_dt_str}
            
            【指示】
            ・名阪国道や各地の無料バイパス（23号、新4号等）の活用を優先的に検討してください。
            ・深夜割引や渋滞状況を考慮したアドバイスを含めてください。
            ・最後に「時間・高速料金・総コスト」の比較表を必ず作成してください。
            """
            
            with st.spinner("AIが最適なルートを計算中..."):
                response = model.generate_content(prompt)
                
                if response and response.text:
                    st.markdown("---")
                    st.write(f"### 🕒 {dep_dt_str} 出発の提案")
                    st.markdown(response.text)
                else:
                    st.error("AIから回答が返ってきませんでした。もう一度お試しください。")

        except Exception as e:
            st.error("AIとの通信に失敗しました。")
            # 詳細なエラーが404なら、モデル名の指定を強制変更してリトライ
            if "404" in str(e):
                st.info("システムの自動修復を試みています。再度ボタンを押してください。")
                model = genai.GenerativeModel(model_name='models/gemini-1.5-flash')
            else:
                st.info(f"詳細なエラー: {e}")

import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. API・モデル設定 (404エラー対策済み) ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    """現在利用可能な最新のGeminiモデルを自動選択"""
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間の計算 (初期値用) ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.markdown("シンプル入力モード")

# --- 3. 入力フォーム ---
st.subheader("📍 ルート設定")

# 全て手入力に統一
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅、栃木県宇都宮市本町など")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（オプション）"):
    v1 = st.text_input("経由地1", placeholder="なし")
    v2 = st.text_input("経由地2", placeholder="なし")

st.write("🚗 車種とコスト設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

st.write("🕒 出発日時")
c1, c2 = st.columns(2)
with c1:
    # カレンダーから自由に選択可能
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # 時刻を自由に選択可能
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AIルート提案の実行 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    elif not destination:
        st.warning("目的地を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        
        prompt = f"""
        あなたはプロのルートガイドです。以下の条件で最適なルートを3つ提案してください。
        
        【条件】
        出発地：{start_point}
        目的地：{destination}
        経由地：{v1}, {v2}
        出発日時：{dt_str}
        車種：{vehicle}
        ユーザーの時間価値：{time_val}円/h
        
        【ルール】
        1. 高速料金：100km以下：(24.6円*Km+150円)*1.1、軽自動車20%引。
        2. 有料道路は :red[○○IC〜××IC]、一般道は :blue[国道○号] のように色分け。
        3. 最後に「時間、高速代、ガソリン代、時間価値コスト」を合計した「総コスト」の比較表を必ず作成。
        
        提案：①タイパ優先 ②コスパ優先 ③バランス優先
        """

        with st.spinner("AIがルートを計算しています..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f"### 🕒 {dt_str} 出発の提案")
                st.markdown(res.text)
                st.caption(f"powered by {model.model_name}")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

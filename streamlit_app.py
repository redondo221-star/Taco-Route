import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
MODEL_NAME = 'gemini-pro'

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間の現在時刻 ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.markdown("### 安定動作モード")

# --- 3. 出発日・出発時刻の初期化（最初の1回だけ） ---
if "dep_date" not in st.session_state:
    st.session_state.dep_date = now_jst.date()

if "dep_time" not in st.session_state:
    st.session_state.dep_time = now_jst.time()

# --- 4. 入力フォーム ---
st.subheader("📍 ルート・コスト設定")

start_point = st.text_input("出発地点", placeholder="例：東京駅、または現在地の住所")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（オプション）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

# --- 5. 出発日時（key を分離して Duplicate 回避） ---
st.write("🕒 出発日時を選択（タップして変更可能）")
c1, c2 = st.columns(2)
with c1:
    st.date_input(
        "出発日",
        key="dep_date_input",
        value=st.session_state.dep_date
    )
with c2:
    st.time_input(
        "出発時刻",
        key="dep_time_input",
        value=st.session_state.dep_time
    )

# --- 6. session_state に反映 ---
st.session_state.dep_date = st.session_state.dep_date_input
st.session_state.dep_time = st.session_state.dep_time_input

# --- 7. AIルート提案 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
    else:
        dt_str = f"{st.session_state.dep_date.strftime('%Y/%m/%d')} {st.session_state.dep_time.strftime('%H:%M')}"

        prompt = f"""
        条件：出発{start_point}、目的地{destination}、日時{dt_str}
        経由地：{v1}, {v2}
        車種：{vehicle}
        時間価値：{time_val}円/h
        
        【ルール】
        1. 高速料金：100km以下：(24.6円*Km+150円)*1.1、軽自動車20%引。
        2. 有料は[RED]、一般道は[BLUE]でルートを記載。
        3. 総コスト（料金＋時間×価値）の比較表を出す。
        
        ルート案：①タイパ優先 ②コスパ優先 ③バランス優先
        """

        with st.spinner("AIが最適なルートを計算中..."):
            try:
                model = genai.GenerativeModel(MODEL_NAME)
                res = model.generate_content(prompt)
                answer = res.text

                # 色付け
                answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
                answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
                answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路)', r':red[\1]', answer)
                answer = re.sub(r'(一般道|国道|バイパス)', r':blue[\1]', answer)

                st.markdown("---")
                st.markdown(f"### 🕒 {dt_str} 出発の提案")
                st.markdown(answer)

            except Exception as e:
                st.error(f"エラーが発生しました。時間をおいて再度お試しください。({e})")

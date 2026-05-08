import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta

# --- 1. API・モデル設定 (最も安定したモデルを指定) ---
MODEL_NAME = 'gemini-pro'

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間を計算 (サーバーの5月8日設定を無視して「今日」を出す) ---
# サーバーがどの日付になっていても、UTCから日本時間を算出して初期値にします
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.markdown("### 安定動作モード")

# --- 3. 入力フォーム ---
st.subheader("📍 ルート・コスト設定")

# 位置情報：自動取得はフリーズの原因になるため、手入力を基本にします
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

# --- 🕒 出発日時の設定 (ここが手動で自由に変更できます) ---
st.write("🕒 出発日時を選択（タップして変更可能）")
c1, c2 = st.columns(2)
with c1:
    # 初期値を「日本時間の今日」に固定。カレンダーから自由に変更できます
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # 初期値を「日本時間の今」に固定。自由に変更できます
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AIルート提案の実行 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        
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

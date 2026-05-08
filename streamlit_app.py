import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
# 404エラーを回避するため、最も安定している名称を使用
MODEL_NAME = 'gemini-pro'

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間を計算（サーバーの5月8日を無視する） ---
# サーバーがどの日付であっても、UTCから日本時間を算出して「今日の初期値」にします
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")

# --- 3. 入力フォーム ---
st.subheader("📍 ルート・コスト設定")

# 無限ループの原因となる自動取得を廃止し、安定性を優先
start_point = st.text_input("出発地点", placeholder="例：東京駅、または現在地の住所")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（オプション）"):
    v1 = st.text_input("経由地1")
    v2 = st.text_input("経由地2")

st.write("🚗 車種とコストの設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

# --- 🕒 出発日時の設定（ここが自由に変更可能になります） ---
st.write("🕒 出発日時を選択（自由に変更できます）")
c1, c2 = st.columns(2)
with c1:
    # 初期値を計算した「日本時間の今日」に設定
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # 初期値を計算した「日本時間の今」に設定
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AI実行 ---
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
        1. 高速料金計算：100km以下：(24.6円*Km+150円)*1.1
        2. 軽自動車は普通車の20%割引
        3. 有料は[RED]、一般道は[BLUE]でルートを表示。
        4. 最後に「有料料金＋（時間×時間価値）」の合計コストを比較表で出す。
        
        ルート案：
        ①タイパ優先、②コスパ優先、③バランス優先（無料バイパス活用）
        """

        with st.spinner("AIがルートを計算中..."):
            try:
                model = genai.GenerativeModel(MODEL_NAME)
                res = model.generate_content(prompt)
                answer = res.text
                
                # 色付け処理
                answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
                answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
                answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路)', r':red[\1]', answer)
                answer = re.sub(r'(一般道|国道|バイパス)', r':blue[\1]', answer)

                st.markdown("---")
                st.markdown(f"### 🕒 {dt_str} 出発の提案")
                st.markdown(answer)
            except Exception as e:
                st.error(f"AIエラー: {e}")

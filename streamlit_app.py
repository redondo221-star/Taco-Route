import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta

# --- 💡 1. モデル名を最も安定している 'gemini-pro' に固定 ---
MODEL_NAME = 'gemini-pro'

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 💡 2. 日付・時刻の補正 ---
# サーバーの時刻が5月8日固定なら、手動で今日の日付を入れられるようにしつつ、
# デフォルトで「日本時間」を計算してセットします。
now_utc = datetime.utcnow()
now_jst = now_utc + timedelta(hours=9)

st.title("🚗 Taco-Route")

# --- 💡 3. メイン画面 ---
st.subheader("📍 ルート・コスト設定")

# 位置情報取得が不安定なため、出発地は空欄（または前回の値）にして手動入力を促します
start_point = st.text_input("出発地点", placeholder="例：東京駅、または現在地の住所を入力")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地設定"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500)

# 日付・時刻の入力（ここで「今日の日付」が正しく入るように補正）
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 💡 4. AI実行 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str}
    車種：{vehicle}
    時間価値：{time_val}円/h
    
    ETC使用前提。
    以下の計算式を厳守して各ルートを提案してください。
    【計算ルール】
    - 高速料金：100km以下：(24.6円*Km+150円)*1.1
    - 軽自動車は普通車の20%割引
    
    【提案ルート】
    1.【タイパ案】最短時間。高速フル活用。有料区間は [RED]、一般道は [BLUE]
    2.【コスパ案】一般道優先。[BLUE]
    3.【バランス案】無料バイパス優先。
    最後にルート比較表を出してください。
    """

    with st.spinner("AIが計算中..."):
        try:
            # 404エラーを回避するため gemini-pro を使用
            model = genai.GenerativeModel(MODEL_NAME)
            res = model.generate_content(prompt)
            answer = res.text
            
            # 色付け
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            st.markdown("---")
            st.markdown(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")
            st.info("APIキーの設定や、Google AI Studioでのモデルの有効化を確認してください。")

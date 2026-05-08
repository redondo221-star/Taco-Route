import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta

# --- 1. モデル名を最も安定している旧名称に固定 ---
MODEL_NAME = 'gemini-pro'

# APIキーの設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])
else:
    st.error("APIキーが設定されていません。")

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間の「今日・今」を計算 ---
# サーバーの時刻に関わらず、UTC+9時間で日本の現在時刻を算出
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.info("※現在地・時刻の自動取得を停止し、手動変更を優先する安定モードで動作中です。")

# --- 3. 入力フォーム ---
st.subheader("📍 ルート・コスト設定")

# 現在地は住所または地名を手入力
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅、現在地の住所など")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（オプション）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/1時間)", value=1500, step=100)

# --- 🕒 出発日時の設定 (ここが自由に変更可能になります) ---
st.write("🕒 出発日時を選択してください")
c1, c2 = st.columns(2)
with c1:
    # 初期値を「日本の今日」に設定。カレンダーで自由に変更可能
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # 初期値を「日本の今」に設定。自由に変更可能
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AIルート提案の実行 ---
if st.button("🚀 この条件でルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
        st.stop()

    # 日時を文字列に変換
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"""
    あなたはルートガイドです。以下の条件で最適な3つのルートを提案してください。
    
    【条件】
    出発地：{start_point}
    目的地：{destination}
    経由地：{v1}, {v2}
    出発日時：{dt_str}
    車種：{vehicle}
    ユーザーの時間価値：{time_val}円/h
    
    【ルール】
    1. 高速料金を概算してください（100km以下：(24.6円*Km+150円)*1.1、軽自動車は20%引）。
    2. 有料道路（高速）は [RED]、一般道・バイパスは [BLUE] でルート詳細を記載してください。
    3. 最後に、有料料金と（時間×時間価値）を合計した「総コスト」を比較する表を作成してください。
    
    提案ルート：
    ①タイパ優先（高速多用）
    ②コスパ優先（一般道メイン）
    ③バランス優先（無料バイパス活用）
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            # 安定したモデル名 'gemini-pro' を使用
            model = genai.GenerativeModel(MODEL_NAME)
            res = model.generate_content(prompt)
            answer = res.text
            
            # 色付け
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.markdown(f"### 🕒 {dt_str} 出発のルート提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"AIとの通信に失敗しました。時間をおいて再度お試しください。({e})")

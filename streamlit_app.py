import streamlit as st
import google.generativeai as genai
import re
import requests
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
# 利用可能なモデルに変更（404 回避）
MODEL_NAME = "gemini-1.5-flash"  # 必要なら "gemini-1.5-pro" などに変更

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間の現在時刻 ---
now_jst = datetime.utcnow() + timedelta(hours=9)
today_jst = now_jst.date()

st.title("🚗 Taco-Route")
st.markdown("### 安定動作モード")

# --- 3. 現在地（IPベース）の取得関数 ---
def get_ip_location():
    try:
        res = requests.get("https://ipinfo.io/json", timeout=3)
        data = res.json()
        city = data.get("city") or ""
        region = data.get("region") or ""
        loc = f"{city}{region}"
        return loc if loc.strip() else ""
    except Exception:
        return ""

# --- 4. session_state 初期化 ---

# 出発日：初回 or 「過去の日付」の場合は今日に更新
if "dep_date" not in st.session_state or st.session_state.dep_date < today_jst:
    st.session_state.dep_date = today_jst

# 出発時刻：初回だけ「今」にする（その後はユーザーの変更を保持）
if "dep_time" not in st.session_state:
    st.session_state.dep_time = now_jst.time()

# 出発地点：初回だけ現在地（IPベース）を入れる
if "start_point" not in st.session_state:
    st.session_state.start_point = get_ip_location()

# --- 5. 入力フォーム ---
st.subheader("📍 ルート・コスト設定")

start_point = st.text_input(
    "出発地点",
    value=st.session_state.start_point,
    placeholder="例：東京駅、または現在地の住所",
    key="start_point_input",
)
st.session_state.start_point = start_point  # 手動変更を保持

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

# --- 6. 出発日時（ユーザー変更を保持しつつ、初期値は「今」） ---
st.write("🕒 出発日時を選択（タップして変更可能）")
c1, c2 = st.columns(2)
with c1:
    st.date_input(
        "出発日",
        key="dep_date_input",
        value=st.session_state.dep_date,
    )
with c2:
    st.time_input(
        "出発時刻",
        key="dep_time_input",
        value=st.session_state.dep_time,
    )

# ウィジェットの値を正式な dep_date / dep_time として採用
st.session_state.dep_date = st.session_state.dep_date_input
st.session_state.dep_time = st.session_state.dep_time_input

# --- 7. AIルート提案 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not st.session_state.start_point:
        st.error("出発地点を入力してください。")
    else:
        dep_date = st.session_state.dep_date
        dep_time = st.session_state.dep_time
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"

        prompt = f"""
        条件：出発{st.session_state.start_point}、目的地{destination}、日時{dt_str}
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

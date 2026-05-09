import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route Pro", layout="centered")

# --- 2. 日本時間計算（初期値用） ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 車両・コスト詳細設定"):
    v1 = st.text_input("経由地1")
    v2 = st.text_input("経由地2")
    col1, col2 = st.columns(2)
    with col1:
        vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
    with col2:
        # 100円刻みに修正
        time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    input_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # ユーザーが変更した時刻を直接取得
    input_time = st.time_input("出発時刻", value=now_jst.time())

# Python側で日時と曜日を確定（AIの勘違いを防止）
departure_dt = datetime.combine(input_date, input_time)
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[departure_dt.weekday()]
dt_display = departure_dt.strftime('%Y年%m月%d日') + f"({day_of_week}) " + departure_dt.strftime('%H:%M')

# --- 4. 実行ボタン ---
if st.button("🚀 プロの最適ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        # AIへの指示（文字色ルールの徹底）
        prompt = f"""
        あなたは日本中の道路を熟知したベテランドライバーです。
        以下の「指定日時」を絶対基準として、プロの視点でルート提案を行ってください。

        【絶対厳守：出発日時】
        {dt_display} 出発
        （※5月16日は土曜日です。休日割引を考慮してください）

        【絶対厳守：表示ルール】
        1. 高速道路・有料道路の名称や区間は、すべて「赤文字」で表記してください。
           例：:red[東北自動車道]、:red[大泉IC〜練馬IC]
        2. 一般道・高規格道路・バイパスの名称は、すべて「青文字」で表記してください。
           例：:blue[国道4号]、:blue[新4号バイパス]、:blue[名阪国道]

        【走行条件】
        出発地：{start_point} / 目的地：{destination} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【ベテランのルート選定】
        - 信号のない「無料爆速道路（新4号、名阪国道等）」を高速の代替として積極活用。
        - 圏央道より「外環道」の方が効率的な場合は迷わず選択。
        - 案③の「トータル最適」は、時間価値を含めた総コストが最も低く、走りやすいプロ推奨ルートを提示。

        【出力構成】
        案①【最速タイパ】、案②【爆速コスパ】、案③【トータル最適】
        最後に、比較表（数式なし、結果のみ）を出してください。
        """

        with st.spinner(f"検証中: {dt_display}..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"## 🏁 {dt_display} 出発の提案結果")
                st.markdown(res.text)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

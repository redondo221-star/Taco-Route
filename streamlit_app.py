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

# --- 2. 時刻・日付の初期値設定 ---
# 実行時の日本時間を基準にする
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

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
        # 100円刻み
        time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    # keyを設定してセッションに保存
    input_date = st.date_input("出発日", value=st.session_state.now.date(), key="d_input")
with c2:
    # keyを設定してセッションに保存（これで上書きが保持される）
    input_time = st.time_input("出発時刻", value=st.session_state.now.time(), key="t_input")

# 出発日時を一つの文字列に確定させる
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[input_date.weekday()]
full_dt_str = f"{input_date.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

# --- 4. 実行ボタン ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        # AIへの指示（色分けと日時上書きを徹底）
        prompt = f"""
        あなたは日本全国の道路を知り尽くした「伝説のプロドライバー」です。
        ナビ通りではなく、走りやすさとコストを両立したルートを提案してください。

        【重要：シミュレーション日時】
        出発日時：{full_dt_str}
        ※5月16日は土曜日です。AIの内部時計ではなく、この日時と曜日を絶対として交通状況・ETC割引を計算してください。

        【重要：表記ルール】
        1. 高速道路・有料道路（名称・区間）は必ず :red[赤文字] で記載。
           例：:red[東北道]、:red[加須IC〜外環浦和IC]
        2. 一般道・バイパス・高規格道路は必ず :blue[青文字] で記載。
           例：:blue[国道4号]、:blue[新4号バイパス]、:blue[名阪国道]

        【走行条件】
        出発：{start_point} / 到着：{destination} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【ベテランのこだわり】
        - 「新4号」「名阪国道」等の無料爆速区間は高速代わりの主役として扱う。
        - 関東から西へ向かう際、圏央道より「外環道（大泉）」経由が速い場合は迷わず選択。
        - 案③の「トータル最適」は、渋滞リスク・走りやすさ・コストの全てが最高の、プロが選ぶ結論ルートにすること。

        【出力構成】
        案①：最速タイパ / 案②：爆速コスパ / 案③：トータル最適
        最後に比較表（結果の数字のみ）を提示。
        """

        with st.spinner(f"検証中: {full_dt_str}..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                st.markdown(res.text)
            except Exception as e:
                st.error(f"エラー: {e}")

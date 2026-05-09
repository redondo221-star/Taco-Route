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

# --- 2. セッション状態の初期化 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")
st.markdown("### 熟練ドライバー仕様・最適化モデル")

# --- 3. 入力フォーム ---
# 【修正】目的地の初期値を空（""）に変更しました
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

# 経由地の入力
col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("経由地1（必須通過）", placeholder="例：佐野SA")
with col_v2:
    v2 = st.text_input("経由地2（任意）", placeholder="")

with st.expander("🔄 車両・コスト詳細設定"):
    col1, col2 = st.columns(2)
    with col1:
        vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
    with col2:
        time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    input_date = st.date_input("出発日", value=st.session_state.now.date(), key="d_input")
with c2:
    input_time = st.time_input("出発時刻", value=st.session_state.now.time(), key="t_input")

# 出発日時と曜日の計算
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[input_date.weekday()]
full_dt_str = f"{input_date.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

# 経由地のテキスト化
via_points = f"「{v1}」" if v1 else ""
if v2: via_points += f" および 「{v2}」"

# --- 4. 実行ボタン ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        # Geminiへの指示
        prompt = f"""
        あなたは日本中の道路を熟知した「伝説のプロドライバー」です。
        以下の条件をすべて満たすルートを3つ提案してください。

        【絶対命令：経由地の通過】
        指定された経由地 {via_points} は必ず通過してください。これを無視したルートは不可です。

        【絶対命令：出発日時】
        出発日時：{full_dt_str}
        ※曜日に基づくETC割引（休日割引・深夜割引）を正確に反映してください。

        【絶対命令：表記ルール】
        1. 高速道路・有料道路（名称・区間）は必ず :red[赤文字] で記載。
           例：:red[東北道]、:red[加須IC〜外環浦和IC]
        2. 一般道・バイパス・高規格道路は必ず :blue[青文字] で記載。
           例：:blue[国道4号]、:blue[新4号バイパス]、:blue[名阪国道]

        【走行条件】
        出発：{start_point} / 到着：{destination} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【プロの視点】
        - 信号のない「無料爆速区間」を優先。
        - 圏央道より「外環道（大泉）」経由の効率性を厳しくチェック。
        - 案③「トータル最適」は、時間価値、料金、走りやすさ（信号の少なさ）を総合判断した結論を提示。

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
                if v1 or v2:
                    st.success(f"✅ 経由地 {via_points} を反映しました。")
            except Exception as e:
                st.error(f"エラー: {e}")

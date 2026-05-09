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

# --- 2. セッション状態の初期化（時刻保持用） ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")
st.markdown("### 経由地・時刻・色分け完全対応モデル")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

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
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        # 強力な制約を加えたプロンプト
        prompt = f"""
        あなたは日本中の道路を知り尽くした、絶対にミスをしないプロドライバーです。
        ナビが無視しがちな「経由地」を必ず含めた、最高に賢いルートを3つ提案してください。

        【絶対遵守の命令：経由地の通過】
        入力された経由地 {via_points} は必ず通過するルートを作成してください。
        これらを無視したルート提案は絶対に許されません。最短距離から外れても必ず立ち寄ってください。

        【絶対遵守の命令：出発日時】
        出発日時：{full_dt_str}
        ※5月16日は土曜日（休日）です。AIの内部時計ではなく、この日時と曜日を基準に交通状況と休日割引を計算してください。

        【絶対遵守の命令：表記ルール】
        1. 高速道路・有料道路の区間・名称は必ず :red[赤文字] で記載。
           例：:red[東北道]、:red[加須IC〜外環浦和IC]
        2. 一般道・バイパス・高規格道路の名称は必ず :blue[青文字] で記載。
           例：:blue[国道4号]、:blue[新4号バイパス]、:blue[名阪国道]

        【走行条件】
        出発：{start_point} / 到着：{destination} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【ベテランのこだわり】
        - 「新4号」「名阪国道」等の無料爆速区間は、高速代わりの主役として活用。
        - 関東圏は「外環道（大泉）」経由の効率性を重視。
        - 案③「トータル最適」は、時間価値、料金、走りやすさのバランスが最も優れた「プロの結論」を提示。

        【出力構成】
        案①：最速タイパ / 案②：爆速コスパ / 案③：トータル最適
        最後に比較表（結果の数字のみ）を提示。
        """

        with st.spinner(f"経由地を確認し、{full_dt_str} のルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                st.markdown(res.text)
                if v1 or v2:
                    st.success(f"✅ 経由地 {via_points} を含むルートを生成しました。")
            except Exception as e:
                st.error(f"エラー: {e}")

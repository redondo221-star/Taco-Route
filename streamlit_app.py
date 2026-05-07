import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime
from streamlit_js_eval import get_geolocation

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 1. 現在地取得（最優先） ---
st.write("📍 現在地を確認中...")
loc = get_geolocation()
current_lat_lon = ""

if loc and 'coords' in loc:
    current_lat_lon = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
    st.success("現在地を捕捉しました。出発地点に反映します。")

# --- 💡 2. 入力フォーム ---
st.subheader("ルート設定")

# 現在地が取れればそれを初期値に
start_point = st.text_input("出発地点", value=current_lat_lon, placeholder="例：東京駅 または 現在地（自動入力待ち）")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

# --- 💡 3. 日時設定（5月7日問題を強制回避） ---
st.warning("⚠️ サーバーの日時が狂っているため、カレンダーから正しい日時を選んでください。")
c1, c2 = st.columns(2)
with c1:
    # 初期値をNoneにすることで、サーバーの狂った5月7日を表示させません
    dep_date = st.date_input("出発日を選択", value=None)
with c2:
    dep_time = st.time_input("出発時刻を選択")

if st.button("ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()
    if dep_date is None:
        st.error("出発日をカレンダーから選択してください。")
        st.stop()

    vias = [v for v in [v1, v2] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # AIへの「究極の指示」
    prompt = f"""
    出発地点：{start_point}
    目的地：{destination}
    出発日時：{dt_str}
    {via_info}

    以下の3つのルートを詳細に提案し、最後に比較表を出してください。

    1.【タイパ案】
    - 有料道路・高速道路を最大限に使用し、最短時間で到着する。
    - 高速道路・有料道路の区間は必ず [RED]...[/RED] で囲む。

    2.【コスパ案】
    - 有料道路は一切禁止。100%一般道（下道）のみで走行。
    - 一般道の区間は必ず [BLUE]...[/BLUE] で囲む。

    3.【バランス案（地元推奨・爆速下道）】
    - 「名阪国道」「新4号バイパス」「上武道路」「保土ヶ谷バイパス」など、信号が少なく、制限速度や実勢速度が速い『無料の高規格道路』を積極的に活用。
    - 地元民が高速代を浮かせるために使う、高速並みに速いルートを提案。
    - 有料区間は [RED]、無料の高規格道・一般道は [BLUE] で囲む。
    """

    with st.spinner("AIがルートを計算中..."):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            res = model.generate_content(prompt)
            answer = res.text
            
            # --- 💡 色付け処理（タグ＋重要単語） ---
            # タグ変換
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            # 単語で強制着色（ルート説明部分の視認性アップ）
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路|自動車専用道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"エラー: {e}")

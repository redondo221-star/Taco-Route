import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 1. ブラウザの現在日時をJavaScriptで取得 ---
# サーバーの2026/05/08を完全に無視するため、ブラウザの「生の日時」を直接取ります
js_now = streamlit_js_eval(js_expressions="new Date().toISOString()", key='js_full_date_v3')

# --- 💡 2. 高精度な位置情報の取得 ---
st.sidebar.markdown("### 🛰️ 位置情報設定")
if st.sidebar.button("現在地を更新"):
    st.rerun()

# 精度を高めるためのオプションを指定して現在地を取得
loc = get_geolocation()

# --- 💡 3. 日付と時刻の確定ロジック ---
if js_now:
    # ブラウザのUTCをJST(+9時間)に変換
    current_dt = datetime.fromisoformat(js_now.replace('Z', '+00:00')) + timedelta(hours=9)
    # 確実に「今日」の日付と「今」の時刻をセット
    default_date = current_dt.date()
    default_time = current_dt.time()
else:
    # JavaScriptがまだ反応していない場合は一時的にNone（空）にする
    default_date = None
    default_time = None

# --- 💡 4. 入力画面 ---
st.subheader("📍 ルート・コスト設定")

# 現在地の反映
start_val = ""
if loc and 'coords' in loc:
    start_val = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"
else:
    start_val = ""

# 出発地点の入力（現在地が取れていれば自動入力）
start_point = st.text_input("出発地点", value=start_val, placeholder="現在地取得中...（住所入力も可）")

if not start_val:
    st.caption("⚠️ 現在地が自動取得されない場合は、ブラウザの位置情報許可を確認するか、直接住所を入力してください。")

destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を設定する"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col_v1, col_v2 = st.columns(2)
with col_v1:
    vehicle_type = st.radio("車種を選択", ["普通車", "軽自動車"], horizontal=True)
with col_v2:
    time_value = st.number_input("時間価値 (円/1時間)", value=1500, step=100)

# --- 🕒 日時設定（ブラウザ時刻を強制反映） ---
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=default_date)
with c2:
    dep_time = st.time_input("出発時刻", value=default_time)

if not js_now:
    st.warning("🕒 ブラウザの時刻を同期中... 数秒待っても日付が変わらない場合は、一度ページを更新してください。")

if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()
    if dep_date is None:
        st.error("出発日が正しく設定されていません。カレンダーから選んでください。")
        st.stop()

    vias = [v for v in [v1, v2] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    車種：{vehicle_type}
    ユーザーの時間価値：1時間あたり {time_value} 円
    
    ETCを使用する前提でコストやICを選択すること。
    高速道路料金の計算：
    - 100km以下：(24.6円 * Km + 150円) * 1.1
    - 100km〜200kmの区間：距離比例料金を25%割引　全体の距離料金を割り引くわけではない
    - 200km以上の区間：距離比例料金を30%割引
    - 土日・夜間割引を考慮
    - 軽自動車は、普通車の料金から20%割引
    
    以下の3ルートを提案し、各ルートの「有料料金＋（時間×時間価値）」の合計コストを計算して比較表を出してください。
    
    1.【タイパ案】最短時間優先。高速フル活用。[RED]高速区間[/RED]
    2.【コスパ案】一般道優先。[BLUE]一般道区間[/BLUE]
    3.【バランス案（地元推奨）】爆速無料バイパス（名阪国道、新4号等）を優先。
       有料は [RED]、無料の高規格道は [BLUE] で囲む。
       高速代がユーザーの時間価値より高い場合は、一般道を提案。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            model_names = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            selected_model = next((m for m in model_names if 'gemini-1.5-flash' in m), model_names[0])
            model = genai.GenerativeModel(selected_model)
            res = model.generate_content(prompt)
            answer = res.text
            
            # 色付け処理
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"AIエラー: {e}")

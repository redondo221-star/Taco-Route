import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 💡 1. JavaScriptによる【完全自動】取得 ---
# 画面が開いた際、ブラウザから緯度、経度、現在日時(ISO)を一度に取得します
js_code = """
(async () => {
    const pos = await new Promise((res, rej) => {
        navigator.geolocation.getCurrentPosition(res, rej, {enableHighAccuracy: true});
    });
    return {
        lat: pos.coords.latitude,
        lon: pos.coords.longitude,
        iso: new Date().toISOString()
    };
})()
"""

# データを取得（一回だけ実行されるようにキーを固定）
browser_data = streamlit_js_eval(js_expressions=js_code, key='get_browser_info_auto')

# --- 💡 2. 取得したデータをPython変数に反映 ---
# 初期値（取得できるまでの予備）
auto_start = ""
now = datetime.now() 

if browser_data and isinstance(browser_data, dict):
    # 位置情報
    auto_start = f"{browser_data.get('lat')}, {browser_data.get('lon')}"
    # 日時（UTCを日本時間に変換）
    iso_str = browser_data.get('iso')
    if iso_str:
        now = datetime.fromisoformat(iso_str.replace('Z', '+00:00')) + timedelta(hours=9)

# --- 💡 3. メイン画面の構成 ---
st.title("🚗 Taco-Route")
st.subheader("📍 自動同期済み設定")

# 取得状況のステータス表示
if browser_data:
    st.success("✅ スマホの現在地・現在時刻を自動反映しました")
else:
    st.info("🕒 スマホと同期中...（位置情報の許可をお願いします）")

# 入力欄（取得された値が初期値として入ります）
start_point = st.text_input("出発地点", value=auto_start, placeholder="現在地を取得しています...")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を設定する"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col1, col2 = st.columns(2)
with col1:
    vehicle_type = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_value = st.number_input("時間価値 (円/h)", value=1500)

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now.time())

# --- 💡 4. AIルート提案実行 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point or start_point == "":
        st.warning("出発地点が空欄です。手入力するか、位置情報を許可してください。")
        st.stop()

    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    via_info = f"（経由地：{v1} {v2}）" if v1 or v2 else ""
    
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    車種：{vehicle_type}
    ユーザーの時間価値：1時間あたり {time_value} 円
    
    ETC使用前提。
    高速道路料金計算：
    - 100km以下：(24.6円 * Km + 150円) * 1.1
    - 100km〜200km：距離料金25%割引　この区間の距離比例料金のみ割り引く　全体の料金を割り引くわけではない
    - 200km以上：距離料金30%割引　この区間の距離比例料金のみ割り引く　全体の料金を割り引くわけではない
    - 軽自動車は普通車の20%割引
    
    以下の3ルートを詳細に提案し、比較表を出してください。
    1.【タイパ案】最短時間優先。高速フル活用。[RED]高速区間[/RED]
    2.【コスパ案】一般道優先。[BLUE]一般道区間[/BLUE]
    3.【バランス案（地元推奨）】爆速無料バイパス（名阪国道、新4号等）を優先。
       有料は [RED]、無料高規格道は [BLUE] で囲む。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            model = genai.GenerativeModel('gemini-1.5-flash')
            res = model.generate_content(prompt)
            answer = res.text
            
            # 色付け
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
        except Exception as e:
            st.error(f"エラー: {e}")

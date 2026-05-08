import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
import pandas as pd
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 1. ブラウザの現在時刻をJavaScriptで取得 ---
# これにより、サーバーの狂った時間ではなく、手元のスマホの時間が取れます
js_time_raw = streamlit_js_eval(js_expressions="new Date().toISOString()", key='browser_time')

# --- 💡 2. 位置情報の取得 ---
loc = get_geolocation()
default_start = ""
if loc and 'coords' in loc:
    default_start = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"

# --- 💡 3. 入力画面 ---
st.subheader("📍 ルート・コスト設定")

start_point = st.text_input("出発地点", value=default_start, placeholder="現在地取得中...")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を設定する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

st.write("🚗 車種とコストの設定")
col_v1, col_v2 = st.columns(2)
with col_v1:
    vehicle_type = st.radio("車種を選択", ["普通車", "軽自動車"], horizontal=True)
with col_v2:
    time_value = st.number_input("時間価値 (円/1時間)", value=1500, step=100)

# --- 💡 4. 日時設定（ブラウザ時刻を反映） ---
# JSから取得した時間をPythonのdatetime型に変換
now = datetime.now()
if js_time_raw:
    try:
        # ISO形式を変換 (UTCなので日本時間に+9時間調整)
        now = datetime.fromisoformat(js_time_raw.replace('Z', '+00:00')) + timedelta(hours=9)
    except:
        pass

st.info(f"🕒 現在のブラウザ時刻を読み込みました")
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now.time())

if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # AIへの指示（ご指定のロジック）
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    車種：{vehicle_type}
    ユーザーの時間価値：1時間あたり {time_value} 円
    
    ETCを使用する前提でコストやICを選択すること。
    高速道路料金の計算：
    - 100km以下：(24.6円 * Km + 150円) * 1.1
    - 100km〜200km：上記走行距離当たり料金を25%割引
    - 200km以上：上記走行距離当たり料金を30%割引
    - 土日割引や夜間割引も考慮すること
    - 軽自動車は、普通車の料金から20%割引すること
    
    以下の3ルートを詳細に提案し、各ルートの「有料料金＋（時間×時間価値）」の合計コストを計算して比較表を出してください。
    
    1.【タイパ案】最短時間優先。高速フル活用。[RED]高速区間[/RED]
    2.【コスパ案】一般道優先。[BLUE]一般道区間[/BLUE]
    3.【バランス案（地元推奨）】名阪国道、新4号バイパス等の「爆速無料バイパス」を優先。
       有料は [RED]、無料の高規格道・一般道は [BLUE] で囲む。
       高速道路と一般道路を比較し、ユーザーの時間価値より高速道路料金が高い場合は、一般道を使うルートを提案すること。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            # 利用可能なモデルを自動検出
            model_names = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            selected_model = next((m for m in model_names if 'gemini-1.5-flash' in m), model_names[0])
            
            model = genai.GenerativeModel(selected_model)
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
            st.error(f"AIエラー: {e}")

import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime
from streamlit_js_eval import get_geolocation, streamlit_js_eval

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 1. 位置情報とブラウザ時刻の取得 ---
loc = get_geolocation()
js_time_str = streamlit_js_eval(js_expressions="new Date().toLocaleString('ja-JP')", key='browser_now')

# --- 💡 2. 入力画面 ---
st.subheader("📍 ルート・コスト設定")

# 現在地の反映
default_start = ""
if loc and 'coords' in loc:
    default_start = f"{loc['coords']['latitude']}, {loc['coords']['longitude']}"

start_point = st.text_input("出発地点", value=default_start, placeholder="現在地取得中...")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

# 経由地設定（復活）
with st.expander("🔄 経由地を設定する（最大3つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")
    v3 = st.text_input("経由地3", key="v3")

# 時間当たりのコスト設定（復活）
st.write("💰 コスト設定")
time_value = st.slider("時間価値（1時間あたりの金額）", 0, 10000, 1500)

# 日時設定（5月7日問題対策）
st.info(f"🕒 ブラウザ時刻: {js_time_str if js_time_str else '取得中...'}")
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日")
with c2:
    dep_time = st.time_input("出発時刻")

if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    vias = [v for v in [v1, v2, v3] if v]
    via_info = f"（経由地：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # AIへの指示（時間価値を考慮させる）
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    ユーザーの時間価値：1時間あたり {time_value} 円
    
    以下の3ルートを提案し、各ルートの「有料料金＋（時間×時間価値）」の合計コストを計算して比較表を出してください。
    
    1.【タイパ案】最短時間優先。高速フル活用。[RED]高速区間[/RED]
    2.【コスパ案】一般道優先。[BLUE]一般道区間[/BLUE]
    3.【バランス案（地元推奨）】名阪国道、新4号バイパス等の「爆速無料バイパス」を優先。
       有料は [RED]、無料の高規格道・一般道は [BLUE] で囲む。高速道路と一般道路を比較し、ユーザーの時間価値より高速道路料金が高い場合は、一般道を使うルートを提案する。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            # 💡 3. 利用可能なモデルを自動検出してエラー回避
            model_names = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
            # gemini-1.5-flashがあれば使い、なければリストの最初を使う
            selected_model = next((m for m in model_names if 'gemini-1.5-flash' in m), model_names[0])
            
            model = genai.GenerativeModel(selected_model)
            res = model.generate_content(prompt)
            answer = res.text
            
            # --- 💡 4. 色付け処理 ---
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            # 強制単語色付け（保険）
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案（時間価値: {time_value}円/h）")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"AIエラーが発生しました: {e}")

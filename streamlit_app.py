import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --- 1. API・モデル設定 (404対策済) ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if 'gemini-1.5-flash' in m), 
                 next((m for m in models if 'gemini-1.5-pro' in m), models[0]))
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 現在地取得用のJavaScriptコンポーネント ---
# ボタンを押すとブラウザのGPSを呼び出し、StreamlitのURLパラメータに値を渡す仕組み
def location_button():
    st.markdown("### 📍 位置情報の取得")
    components.html(
        """
        <button id="loc_btn" style="
            background-color: #ff4b4b; 
            color: white; 
            border: none; 
            padding: 10px 20px; 
            border-radius: 5px; 
            cursor: pointer;
            width: 100%;
            font-weight: bold;
        ">🛰️ 現在地を読み込む</button>
        <p id="status" style="font-size: 12px; color: gray;"></p>
        <script>
            const btn = document.getElementById('loc_btn');
            btn.addEventListener('click', () => {
                document.getElementById('status').innerText = "取得中...";
                navigator.geolocation.getCurrentPosition(
                    (pos) => {
                        const lat = pos.coords.latitude;
                        const lon = pos.coords.longitude;
                        // 親ウィンドウ（Streamlit）に値を送る
                        window.parent.postMessage({
                            type: 'streamlit:set_widget_value',
                            data: {value: lat + "," + lon, key: 'geo_input'}
                        }, '*');
                        document.getElementById('status').innerText = "取得完了！";
                    },
                    (err) => {
                        document.getElementById('status').innerText = "エラー: " + err.message;
                    }
                );
            });
        </script>
        """,
        height=100,
    )

# --- 3. メイン画面 ---
st.title("🚗 Taco-Route")

# 日本時間の計算
now_jst = datetime.utcnow() + timedelta(hours=9)

st.subheader("📍 ルート・コスト設定")

# 現在地取得ボタンを配置
location_button()

# 出発地点の入力欄（key='geo_input' で上のJSと連動）
start_point = st.text_input("出発地点", key="geo_input", placeholder="例：東京駅、または上のボタンで取得")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地設定"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500)

st.write("🕒 出発日時")
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AIルート提案の実行 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        prompt = f"""
        条件：出発{start_point}、目的地{destination}、日時{dt_str}
        経由地：{v1}, {v2}
        車種：{vehicle}
        時間価値：{time_val}円/h
        
        【指示】
        1. 高速料金：100km以下は (24.6円*Km+150円)*1.1、軽自動車20%引。
        2. 有料区間は :red[○○IC〜××IC]、一般道は :blue[国道○号] のように記載。
        3. 最後に「時間・高速代・ガソリン代・時間価値コスト」の比較表を出す。
        
        提案：①タイパ案 ②コスパ案 ③バランス案
        """

        with st.spinner("AI計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(res.text.replace("[RED]", ":red[").replace("[/RED]", "]").replace("[BLUE]", ":blue[").replace("[/BLUE]", "]"))
                st.caption(f"powered by {model.model_name}")
            except Exception as e:
                st.error(f"AIエラー: {e}")

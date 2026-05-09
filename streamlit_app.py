import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import streamlit.components.v1 as components

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

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 【超重要】現在地を強制取得するJavaScript ---
# この部品は、ボタンが押されるとスマホのGPSを呼び出し、
# その結果をStreamlitの「出発地点」という箱に直接送り込みます。
def location_fetcher():
    components.html(
        """
        <div style="background-color: #f0f2f6; padding: 15px; border-radius: 10px; border: 1px solid #ddd;">
            <p style="margin: 0 0 10px 0; font-weight: bold; font-family: sans-serif; font-size: 14px;">📍 現在地ボタン</p>
            <button id="get-location" style="
                width: 100%;
                padding: 12px;
                background-color: #ff4b4b;
                color: white;
                border: none;
                border-radius: 5px;
                font-weight: bold;
                cursor: pointer;
            ">🛰️ 現在地を取得して入力する</button>
            <p id="status" style="margin: 8px 0 0 0; font-size: 12px; font-family: sans-serif; color: #666;"></p>
        </div>

        <script>
            const btn = document.getElementById('get-location');
            const status = document.getElementById('status');

            btn.addEventListener('click', () => {
                status.innerText = "GPS測定中...（許可ダイアログが出たら承認してください）";
                if (!navigator.geolocation) {
                    status.innerText = "お使いのブラウザはGPSに対応していません";
                    return;
                }

                navigator.geolocation.getCurrentPosition(
                    (position) => {
                        const lat = position.coords.latitude;
                        const lon = position.coords.longitude;
                        const coords = lat + "," + lon;
                        
                        // Streamlitの入力欄に値を渡す
                        window.parent.postMessage({
                            type: 'streamlit:set_widget_value',
                            data: {value: coords, key: 'start_input'}
                        }, '*');
                        
                        status.innerText = "取得成功！出発地点に入力しました。";
                    },
                    (error) => {
                        status.innerText = "取得失敗: " + error.message + " (設定で位置情報を許可してください)";
                    },
                    { enableHighAccuracy: true }
                );
            });
        </script>
        """,
        height=130,
    )

# --- 3. 画面構成 ---
st.title("🚗 Taco-Route")
now_jst = datetime.utcnow() + timedelta(hours=9)

st.subheader("📍 ルート・コスト設定")

# 現在地取得ボタンを配置（ここが重要！）
location_fetcher()

# 出発地点（key="start_input" にすることで上のJSから値を受け取れる）
start_point = st.text_input("出発地点", key="start_input", placeholder="例：宇都宮駅、または上のボタンを使用")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500)

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AI実行 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        prompt = f"出発地:{start_point}, 目的地:{destination}, 日時:{dt_str}, 車種:{vehicle}, 時間価値:{time_val}円/h ... (以下略)"

        with st.spinner("AIがルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(res.text)
                st.caption(f"使用モデル: {model.model_name}")
            except Exception as e:
                st.error(f"エラー: {e}")

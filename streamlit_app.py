import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import streamlit.components.v1 as components

# --- 1. AIモデル設定 (404対策済み) ---
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

# --- 2. 日本時間の計算 ---
now_jst = datetime.utcnow() + timedelta(hours=9)

# --- 3. 現在地取得 JavaScript (URLパラメータ注入方式) ---
# このJSは、取得した座標をブラウザのURLに「?geo=緯度,経度」としてセットします
def location_script():
    components.html(
        """
        <script>
        const getLocation = () => {
            if (!navigator.geolocation) {
                alert("お使いのブラウザはGPSに対応していません");
                return;
            }
            navigator.geolocation.getCurrentPosition(
                (pos) => {
                    const coords = pos.coords.latitude + "," + pos.coords.longitude;
                    const url = new URL(window.parent.location.href);
                    url.searchParams.set("geo", coords);
                    window.parent.location.href = url.href;
                },
                (err) => {
                    alert("位置情報の取得に失敗しました: " + err.message + "\\nスマホの設定でブラウザの位置情報許可を確認してください。");
                },
                { enableHighAccuracy: true }
            );
        };
        </script>
        <button onclick="getLocation()" style="
            width: 100%; padding: 12px; background-color: #ff4b4b; color: white;
            border: none; border-radius: 5px; font-weight: bold; cursor: pointer;
            box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        ">🛰️ 現在地を今すぐ取得する</button>
        """,
        height=70,
    )

# --- 4. 画面表示 ---
st.title("🚗 Taco-Route")

st.subheader("📍 ルート・コスト設定")

# URLから位置情報を読み取る
query_params = st.query_params
geo_from_url = query_params.get("geo", "")

# 現在地取得ボタン
location_script()

# 出発地点の初期値設定
start_point = st.text_input(
    "出発地点", 
    value=geo_from_url, 
    placeholder="上のボタンを押すか、住所を入力"
)

if geo_from_url:
    st.success(f"✅ 現在地を読み込みました ({geo_from_url})")
else:
    st.info("💡 「現在地ボタン」を押すと、ここに座標が自動入力されます。")

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

# --- 5. AIルート提案 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        prompt = f"""
        あなたは交通のプロです。出発:{start_point}から目的地:{destination}まで、
        日時:{dt_str}、車種:{vehicle}、時間価値:{time_val}円/h でルートを3つ出してください。
        有料道路料金、時間、ガソリン代、そして「時間価値を含めた総コスト」の比較表を最後に必ず付けてください。
        """

        with st.spinner("AIがルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(res.text)
            except Exception as e:
                st.error(f"AIエラー: {e}")

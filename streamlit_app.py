import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- 💡 1. 安全なモデル選択ロジック ---
def get_safe_model():
    try:
        # 最新のモデル名から順に試行
        return genai.GenerativeModel('gemini-1.5-pro')
    except:
        return genai.GenerativeModel('gemini-pro')

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 💡 2. ブラウザから「今」を強制取得するJS ---
# サーバーの5月8日を完全に無視するため、JSが値を返すまで Python 側を停止させます
js_code = """
(async () => {
    const getPos = () => new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, {timeout:5000}));
    let data = { lat: null, lon: null, iso: new Date().toISOString() };
    try {
        const pos = await getPos();
        data.lat = pos.coords.latitude;
        data.lon = pos.coords.longitude;
    } catch (e) {
        console.log("Location error", e);
    }
    return data;
})()
"""

# JSの実行結果を待つ
sync_data = streamlit_js_eval(js_expressions=js_code, key='v10_final_sync')

# 取得できるまで「読み込み中」で画面を止める（これが5月8日対策の肝です）
if not sync_data:
    st.info("🕒 スマホと時刻・位置情報を同期しています... (5秒ほどかかる場合があります)")
    st.stop()

# --- 💡 3. 同期データの解析 ---
# 日本時間に変換
now_jst = datetime.fromisoformat(sync_data['iso'].replace('Z', '+00:00')) + timedelta(hours=9)
auto_latlon = f"{sync_data['lat']}, {sync_data['lon']}" if sync_data['lat'] else ""

# --- 💡 4. メイン画面の表示 ---
st.title("🚗 Taco-Route")
st.success(f"✅ 同期成功: {now_jst.strftime('%Y/%m/%d %H:%M')} の情報を使用中")

start_point = st.text_input("出発地点", value=auto_latlon, placeholder="現在地を取得済み（手入力も可）")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地設定"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col_v1, col_v2 = st.columns(2)
with col_v1:
    vehicle_type = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col_v2:
    time_value = st.number_input("時間価値 (円/h)", value=1500)

c1, c2 = st.columns(2)
with c1:
    # 初期値に、JSから取った「今の正しい日付」をセット
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # 初期値に、JSから取った「今の正しい時刻」をセット
    dep_time = st.time_input("出発時刻", value=now_jst.time())

if st.button("🚀 この条件でルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    via_info = f"（経由地：{' → '.join([v for v in [v1, v2] if v])}）" if v1 or v2 else ""
    
    # プロンプト（指示の完全反映）
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    車種：{vehicle_type}
    ユーザーの時間価値：1時間あたり {time_value} 円
    
    ETC使用前提。
    料金計算：
    - 100km以下：(24.6円*Km+150円)*1.1
    - 100-200km：距離当たり25%割引 / 200km以上：30%割引
    - 軽自動車は普通車の20%割引。土日・夜間割引考慮。
    
    以下の3ルートを提案し比較表を出せ。
    1.【タイパ案】最短時間優先。高速フル活用。[RED]高速[/RED]
    2.【コスパ案】一般道優先。[BLUE]一般道[/BLUE]
    3.【バランス案】無料バイパス優先。高速代が時間価値より高いなら一般道。
    """

    with st.spinner("AIが最適なルートを計算中..."):
        try:
            model = get_safe_model()
            res = model.generate_content(prompt)
            answer = res.text
            
            # 色付け
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号)', r':blue[\1]', answer)

            st.markdown("---")
            st.markdown(f"### 🕒 {dt_str} 出発（{vehicle_type}）")
            st.markdown(answer)
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

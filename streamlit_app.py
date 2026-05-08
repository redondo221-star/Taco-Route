import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta
from streamlit_js_eval import streamlit_js_eval

# --- 💡 1. モデル名の修正 (404エラー対策) ---
# gemini-1.5-flash でエラーが出る環境のため、より汎用的な 'gemini-pro' を優先します
MODEL_NAME = 'gemini-pro' 

if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 💡 2. 自動取得の仕組みを強化 ---
# 緯度・経度・時間を一つのJSオブジェクトとして一気に、かつ強制的に取得します
js_script = """
(async () => {
    const getPos = () => new Promise((res, rej) => navigator.geolocation.getCurrentPosition(res, rej, {enableHighAccuracy: true}));
    try {
        const pos = await getPos();
        return {
            lat: pos.coords.latitude,
            lon: pos.coords.longitude,
            iso: new Date().toISOString(),
            ok: true
        };
    } catch (e) {
        return { iso: new Date().toISOString(), ok: false };
    }
})()
"""

# データの取得（キーを固定して初回に必ず実行）
b_data = streamlit_js_eval(js_expressions=js_script, key='auto_sync_v5')

# データが取れるまで待機し、取れたら変数に格納
if b_data:
    # 日本時間に変換
    now = datetime.fromisoformat(b_data['iso'].replace('Z', '+00:00')) + timedelta(hours=9)
    auto_start = f"{b_data['lat']}, {b_data['lon']}" if b_data.get('ok') else ""
else:
    # 取得中の表示
    st.info("🛰️ スマホと同期しています... 位置情報の許可をお願いします。")
    st.stop() # データが取れるまでここで止めることで「5月8日」が出るのを防ぎます

# --- 💡 3. メイン画面 ---
st.title("🚗 Taco-Route")
st.success("✅ 同期完了：現在地と時刻を反映しました")

start_point = st.text_input("出発地点", value=auto_start)
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（最大2つ）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500)

c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now.time())

# --- 💡 4. AI実行 (プロンプトは維持) ---
if st.button("🚀 最適ルートを提案してもらう"):
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    via_info = f"（経由地：{v1} {v2}）" if v1 or v2 else ""
    
    prompt = f"""
    条件：出発{start_point}、目的地{destination}、日時{dt_str} {via_info}
    車種：{vehicle}
    時間価値：{time_val}円/h
    ETC使用前提。
    料金計算：
    - 100km以下：(24.6円*Km+150円)*1.1
    - 100-200km：25%割引 / 200km以上：30%割引
    - 軽自動車は普通車の20%割引
    
    以下3ルートを詳細に提案し比較表を出して。
    1.【タイパ案】最短時間。高速多用。有料区間は [RED]、一般道は [BLUE]
    2.【コスパ案】一般道優先。[BLUE]
    3.【バランス案】無料バイパス優先。高速代が時間価値より高いなら一般道。
    """

    with st.spinner("AI計算中..."):
        try:
            # モデルを 'gemini-pro' に固定して404を回避
            model = genai.GenerativeModel(MODEL_NAME)
            res = model.generate_content(prompt)
            
            # 色付け
            answer = res.text.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            st.markdown("---")
            st.markdown(answer)
        except Exception as e:
            st.error(f"AIエラーが発生しました。別のモデルを試します... {e}")

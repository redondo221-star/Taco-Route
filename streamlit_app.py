import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. AIモデル設定 (404対策済み・最速モデル) ---
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
current_time_str = now_jst.strftime('%Y年%m月%d日 %H:%M')

st.title("🚗 Taco-Route")
st.info(f"現在時刻: {current_time_str} (日本時間)")

# --- 3. 入力フォーム ---
st.subheader("📍 ルート設定")

# GPS取得が動かないため、デフォルトで「現在地（宇都宮）」と入れておきます。
# これにより、AIが文脈から場所を判断します。
start_point = st.text_input("出発地点", value="現在地 (栃木県宇都宮市)", help="具体的な住所や駅名を入れるとより正確になります")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地設定"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 コスト設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500)

# 日時設定
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. AIルート提案 ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        
        # プロンプトに「現在時刻」と「出発地」を詳しく含めることで、GPSの代わりをさせます
        prompt = f"""
        あなたは交通・物流の専門家です。
        現在、日本時間は {current_time_str} です。
        この時間情報を踏まえ、以下の条件で最適なルートを3つ提案してください。

        【条件】
        出発地：{start_point}
        目的地：{destination}
        経由地：{v1 if v1 else "なし"}, {v2 if v2 else "なし"}
        出発希望日時：{dt_str}
        車種：{vehicle}
        ユーザーの時間価値：{time_val}円/h

        【必須ルール】
        1. 料金計算：100km以下は (24.6円*Km+150円)*1.1。軽自動車は20%引。
        2. 出発地が「現在地」とある場合は、宇都宮付近を起点として計算してください。
        3. 有料道路は :red[○○IC〜××IC]、一般道は :blue[国道○号] と表記。
        4. 最後に比較表（時間、高速代、ガソリン代、総コスト）を出してください。
        """

        with st.spinner("AIがルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(res.text)
                st.success("AIが現在時刻と場所を考慮してルートを生成しました。")
            except Exception as e:
                st.error(f"AIエラー: {e}")

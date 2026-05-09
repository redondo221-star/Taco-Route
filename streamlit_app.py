import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

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

# --- 2. 日本時間計算 ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")
st.markdown("### コスパ・タイパ最適化ルート提案")

# --- 3. 入力フォーム ---
with st.container():
    st.subheader("📍 目的地と出発地")
    start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
    destination = st.text_input("目的地", value="ルートイン和泉岸和田")

    with st.expander("🔄 経由地・車両設定"):
        v1 = st.text_input("経由地1")
        v2 = st.text_input("経由地2")
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

# --- 4. AIルート提案（プロンプト強化版） ---
if st.button("🚀 最適ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        
        # 指示書の強化：高規格道路の利用とNexco料金の適用を明記
        prompt = f"""
        あなたは日本の道路事情に精通した熟練のルートプランナーです。
        以下の条件で、ユーザーが唸るような「賢いルート」を3つ提案してください。

        【条件】
        出発地：{start_point} / 目的地：{destination}
        経由地：{v1}, {v2} / 日時：{dt_str} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【ルート選定の極意】
        1. 高規格道路の活用：
           - 単なる高速道路だけでなく、無料の高規格幹線道路、地域高規格道路、地元民が使う流れの速いバイパス（爆速道路）を積極的にルートに組み込んでください。
        2. Nexco料金の準拠：
           - 有料道路の料金はNexcoの最新料金体系（車種別・ETC割引考慮）を反映させて算出してください。
        3. 計算プロセスの省略：
           - 数式や計算式は出力しないでください。結果の数値（料金・時間・コスト）のみをスマートに提示してください。

        【出力構成】
        - 案①：【タイパ優先】有料道路をフル活用し、1分でも早く着くルート。
        - 案②：【コスパ優先】無料の高規格道路やバイパスを駆使し、料金を抑えつつ速度を維持するルート。
        - 案③：【バランス案】時間価値（{time_val}円/h）を考慮し、トータルコストが最小になる賢い選択。

        【表記ルール】
        - 有料区間：:red[○○IC〜××IC]
        - 一般道・高規格：:blue[国道○号・××バイパス]
        - 最後に、時間、高速代、ガソリン代、総コストをまとめた「比較表」を提示してください。
        """

        with st.spinner("最適な爆速ルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f"### 🕒 {dt_str} 出発の提案結果")
                st.markdown(res.text)
                st.caption(f"powered by {model.model_name}")
                
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

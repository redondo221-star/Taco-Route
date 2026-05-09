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

st.set_page_config(page_title="Taco-Route Pro", layout="centered")

# --- 2. 日本時間計算 ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")
st.markdown("### 熟練ドライバーの「走り」を再現する最適ルート提案")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 車両・コスト詳細設定"):
    v1 = st.text_input("経由地1")
    v2 = st.text_input("経由地2")
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

# --- 4. AIルート提案（「走り」の質を最優先したプロンプト） ---
if st.button("🚀 プロの最適ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        
        prompt = f"""
        あなたは、日本中の国道・高速を数百万キロ走り込んできた伝説のトラック運転手、兼、交通コンサルタントです。
        ナビの「最短距離」に騙されず、現場のプロが選ぶ「結果的に一番賢い」ルートを提案してください。

        【条件】
        出発地：{start_point} / 目的地：{destination} / 経由地：{v1}, {v2}
        日時：{dt_str} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【ベテランの鉄則（この通りに考えてください）】
        1. 信号の罠を避ける：
           「新4号」「名阪国道」など、信号がほぼなく実質高速道路として機能している区間を、高速の代替として積極的に組み込むこと。
        2. 都市部の最適接続：
           関東圏では「圏央道」が遠回りになるケースが多い。東北道から都心・関西方面へ抜ける際、「外環道→大泉IC（または首都高）」などの、安くて速いショートカットを優先検討すること。
        3. NEXCO料金の厳守：
           最新のETC割引料金（深夜・休日）を参照し、不必要な高速利用（1区間だけ乗るなど）は避けること。
        4. 総合効率の再定義：
           「トータル最適ルート」とは、単に数式上の数字が低い道ではなく、渋滞リスクが低く、定速で走り続けられ、かつ費用が抑えられる「プロが自腹で走る時に選ぶ道」を指します。

        【出力】
        - 案①：【最速タイパ】金に糸目をつけず、最新の高速ネットワークで1分を削り出す道。
        - 案②：【爆速コスパ】新4号や名阪国道等の「無料爆速区間」を主軸に据え、高速代を半分以下にしつつ時間は最速案に迫る道。
        - 案③：【トータル最適（プロの推奨）】時間価値（{time_val}円/h）を考慮した上で、最もストレスなく、総合コストが最小になる「賢い」道。

        ※計算式は出さず、比較表と各ルートの「なぜこれが賢いのか」の解説のみ記述してください。
        """

        with st.spinner("プロの経験値と最新データを照合中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(res.text)
                st.info("💡 ベテランの視点：距離が短くても信号が多い道より、遠回りでも止まらないバイパスを評価しています。")
            except Exception as e:
                st.error(f"AIエラー: {e}")

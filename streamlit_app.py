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

st.set_page_config(page_title="Taco-Route (Professional Edition)", layout="centered")

# --- 2. 日本時間計算 ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")
st.markdown("ベテランドライバーによる「爆速・最適」ルート提案")

# --- 3. 入力フォーム ---
with st.container():
    start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
    destination = st.text_input("目的地", value="ルートイン和泉岸和田")

    with st.expander("🔄 詳細設定（車種・時間価値）"):
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

# --- 4. AIルート提案（超・ベテラン指示プロンプト） ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
        
        # 指示書の強化：具体的な「爆速道路」の例を挙げ、都市部のショートカットも指示
        prompt = f"""
        あなたは日本全国の道を知り尽くした、配送・長距離輸送のベテランドライバーです。
        ナビが出す単純なルートではなく、実際に走った時に「最も効率が良い」と確信できるルートを3つ提案してください。

        【条件】
        出発地：{start_point} / 目的地：{destination}
        経由地：{v1}, {v2} / 日時：{dt_str} / 車種：{vehicle} / 時間価値：{time_val}円/h

        【ベテランの判断基準】
        1. 「新4号国道」や「名阪国道」など、信号が少なく高速道路並みに巡航できる無料の高規格道路を最優先で検討すること。
        2. 都市部（特に東京圏）では、外環道や中央道、首都高の接続を考慮し、圏央道より「外環道経由」の方が速くて安い場合は迷わずそちらを選択すること。
        3. ETC割引料金（深夜割引・休日割引）を反映したNexco料金を用いること。
        4. 1秒でも早く着く「爆速案」、1円でも安く浮かす「倹約案」、そして時間価値（{time_val}円/h）を計算しトータルコストが最も低い「賢者案」の3つを提示すること。

        【出力構成】
        - 案①：【最速タイパ】有料道路の最短接続を駆使。
        - 案②：【爆速コスパ】無料の高規格バイパスをフル活用し、高速料金を劇的に浮かせつつ時間を維持する。
        - 案③：【トータル最適】時間コストを考慮し、最も「損をしない」ルート。

        【表記ルール】
        - 有料区間：:red[○○IC〜××IC]
        - 一般道・高規格：:blue[国道○号・××バイパス]
        - 計算過程の数式は不要。結果（料金・時間・ガソリン代・総コスト）をまとめた「比較表」のみ提示。
        """

        with st.spinner("プロの視点でルートを検証中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(res.text)
                st.info("※この提案は信号密度や無料高規格道路の利便性を考慮しています。")
                
            except Exception as e:
                st.error(f"エラー: {e}")

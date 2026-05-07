import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime

# API設定
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

st.set_page_config(page_title="Taco-Route", layout="centered")
st.title("🚗 Taco-Route")

# --- 💡 入力画面 ---
st.subheader("ルート設定")

# 現在地取得（js-evalは日時に悪影響を与える可能性があるため一旦外し、シンプルにします）
start_point = st.text_input("出発地点", value="", placeholder="例：西東京市北町")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地を追加する"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

# --- 💡 日時設定（ここが修正の肝） ---
# サーバーの時刻を使わず、あえて固定値を入れず「今日」をユーザーに選ばせる形式にします
st.info("⚠️ サーバーの時刻が狂っているため、出発日時をカレンダーから選んでください")
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("1. 出発日を選んでください")
with c2:
    dep_time = st.time_input("2. 出発時刻を選んでください")

if st.button("ルートを提案してもらう"):
    if not start_point:
        st.error("出発地点を入力してください。")
        st.stop()

    vias = [v for v in [v1, v2] if v]
    via_info = f"（経由：{' → '.join(vias)}）" if vias else ""
    dt_str = f"{dep_date.strftime('%Y/%m/%d')} {dep_time.strftime('%H:%M')}"
    
    # AIへの指示：役割を完全に分ける
    prompt = f"""
    条件：出発{start_point}、到着{destination}、日時{dt_str} {via_info}
    
    以下の3つの異なるルートを提案し、最後に比較表を出せ。
    
    1.【タイパ案】
    最短時間優先。高速道路を最大限使う。
    高速区間の説明は [RED]...[/RED] で囲むこと。

    2.【コスパ案】
    料金0円優先。有料道路は一切使わず、100%一般道（下道）のみ。
    説明は [BLUE]...[/BLUE] で囲むこと。

    3.【バランス案（地元推奨）】
    名阪国道、新4号バイパス、上武道路など、信号が少なく平均速度が速い「無料の高規格道路」を優先的に使う賢いルート。
    有料区間は [RED]、無料区間・バイパスは [BLUE] で囲むこと。
    """

    with st.spinner("AIがルートを分析中..."):
        try:
            model = genai.GenerativeModel("gemini-1.5-flash")
            res = model.generate_content(prompt)
            answer = res.text
            
            # --- 💡 色付けの強制処理 ---
            # AIが付けたタグを変換
            answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
            answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
            
            # タグ付けを忘れた場合のための保険（単語で色付け）
            answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路|PA|SA)', r':red[\1]', answer)
            answer = re.sub(r'(一般道|下道|国道|バイパス|名阪国道|新4号|上武道路)', r':blue[\1]', answer)

            st.markdown("---")
            st.write(f"### 🕒 {dt_str} 出発の提案")
            st.markdown(answer)
            
        except Exception as e:
            st.error(f"エラーが発生しました。APIキーを確認してください。")

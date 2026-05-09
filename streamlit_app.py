import streamlit as st
import google.generativeai as genai
import re
from datetime import datetime, timedelta

# --- 1. API設定と「動くモデル」の自動選択 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    """現在利用可能なモデルの中から最適なものを自動で選ぶ"""
    try:
        # 利用可能なモデルリストを取得
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        # 1.5-flash があれば優先、なければ 1.5-pro、それもなければリストの先頭を使う
        target = next((m for m in models if 'gemini-1.5-flash' in m), 
                 next((m for m in models if 'gemini-1.5-pro' in m), models[0]))
        return genai.GenerativeModel(target)
    except Exception:
        # 万が一リスト取得に失敗した場合の最終手段
        return genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 日本時間を計算 ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route")

# --- 3. 入力フォーム ---
st.subheader("📍 ルート・コスト設定")

start_point = st.text_input("出発地点", placeholder="例：宇都宮駅、または現在地の住所")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 経由地（オプション）"):
    v1 = st.text_input("経由地1", key="v1")
    v2 = st.text_input("経由地2", key="v2")

st.write("🚗 車種とコストの設定")
col1, col2 = st.columns(2)
with col1:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
with col2:
    time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

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
        あなたはプロのルートガイドです。以下の条件で最適な3つのルートを提案してください。
        
        【条件】
        出発地：{start_point}
        目的地：{destination}
        経由地：{v1}, {v2}
        出発日時：{dt_str}
        車種：{vehicle}
        ユーザーの時間価値：{time_val}円/h
        
        【指示】
        1. 高速料金を概算。100km以下：(24.6円*Km+150円)*1.1、軽自動車20%引。
        2. 有料道路（高速）は [RED]、一般道・バイパスは [BLUE] で詳細を記載。
        3. 有料料金と（時間×時間価値）を合計した「総コスト」の比較表を作成。
        
        提案：①タイパ優先 ②コスパ優先 ③バランス優先
        """

        with st.spinner("最新のAIモデルに接続して計算中..."):
            try:
                # 自動選択されたモデルで実行
                model = get_working_model()
                res = model.generate_content(prompt)
                answer = res.text
                
                # 色付け
                answer = answer.replace("[RED]", ":red[").replace("[/RED]", "]")
                answer = answer.replace("[BLUE]", ":blue[").replace("[/BLUE]", "]")
                answer = re.sub(r'(高速道路|IC|インター|JCT|有料道路)', r':red[\1]', answer)
                answer = re.sub(r'(一般道|国道|バイパス)', r':blue[\1]', answer)

                st.markdown("---")
                st.markdown(f"### 🕒 {dt_str} 出発の提案 ({model.model_name})")
                st.markdown(answer)
            except Exception as e:
                st.error(f"AIエラー: {e}")
                st.info("APIキーが有効であること、およびGoogle AI StudioでPay-as-you-go設定が不要な範囲であることを確認してください。")

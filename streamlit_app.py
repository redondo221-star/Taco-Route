import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime, timedelta
import urllib.parse
import re

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    safety_settings = {
        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
    }
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if '1.5-flash' in m), 
                     next((m for m in available_models if '1.5-pro' in m), available_models[0]))
        return genai.GenerativeModel(target, safety_settings=safety_settings)
    except:
        return genai.GenerativeModel('gemini-1.5-flash', safety_settings=safety_settings)

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 画面構成・入力フォーム ---
st.title("🚗 Taco-Route")
st.markdown("### 3ルート完全比較・可視化モデル")

start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地1", placeholder="例：さいたま市")
with col_v2:
    v2 = st.text_input("任意経由地2", placeholder="")

# --- 出発日時の設定（復活） ---
with st.expander("🕒 出発日時・詳細設定", expanded=True):
    col_d, col_t = st.columns(2)
    with col_d:
        input_date = st.date_input("出発日", value=datetime.now().date())
    with col_t:
        input_time = st.time_input("出発時刻", value=datetime.now().time())
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

departure_dt = datetime.combine(input_date, input_time)
full_dt_str = departure_dt.strftime('%Y年%m月%d日 %H:%M')

# --- 3. 実行処理 ---
if st.button("🚀 3つのルートを比較・提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地と目的地を入力してください。")
    else:
        # プロンプト：色分けのCSS適用とIC指定をさらに厳格化
        prompt = f"""
        あなたは日本のプロドライバーです。以下の条件で3つのルートを提案してください。
        出発日時：{full_dt_str}
        出発：{start_point} / 目的地：{destination} / 経由：{v1}, {v2} / 車種：{vehicle}

        【絶対遵守のルール】
        1. ルート解説での色分け：
           - 有料道路・高速区間は必ず `:red[== 道路名 (〇〇IC～××IC) ==]` と表記。
           - 一般道・バイパス区間は必ず `:blue[-- 道路名・バイパス名 --]` と表記。
        2. 比較表の提示：案①最速、案②爆速コスパ、案③トータル最適の距離・時間・料金を比較。
        3. MAP再現用地点の抽出（重要）：
           Googleマップが勝手にルートを変えないよう、各案の「乗るIC入口名」「降りるIC出口名」「バイパスの名称」を5つ以上、正確に抽出してください。

        DATA_START
        ROUTE1_POINTS:{start_point},[乗るIC名1],[主要JCT],[降りるIC名1],{destination}
        ROUTE2_POINTS:{start_point},[バイパス名],[乗るIC名2],[降りるIC名2],[バイパス名],{destination}
        ROUTE3_POINTS:{start_point},[主要経由地],{destination}
        DATA_END
        """

        with st.spinner("最適なICの出入り口を計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                if res.candidates:
                    full_text = res.text
                    display_content = full_text.split("DATA_START")[0]
                    
                    st.markdown("---")
                    st.markdown(f"### 🏁 診断結果 ({full_dt_str} 出発)")
                    
                    # 1. 比較表と色分けルート解説を表示
                    st.markdown(display_content)

                    # 2. 地図ボタンを表示
                    st.subheader("📍 提案ルートをGoogleマップで開く")
                    st.caption("※AIが指定した「乗るIC・降りるIC」を経由地として強制セットしています。")
                    
                    cols = st.columns(3)
                    labels = ["①最速ルート", "②爆速コスパ", "③トータル最適"]
                    
                    data_match = re.search(r"DATA_START(.*?)DATA_END", full_text, re.DOTALL)
                    if data_match:
                        data_part = data_match.group(1)
                        for i, label in enumerate(labels):
                            pattern = f"ROUTE{i+1}_POINTS:(.*)"
                            match = re.search(pattern, data_part)
                            if match:
                                # 地点リストをURL化（経由地を重視するdir形式）
                                pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                                # Google Mapのルート検索URL（/dir/地点1/地点2/...）
                                gmap_base = "https://www.google.com/maps/dir/"
                                query = "/".join([urllib.parse.quote(p) for p in pts])
                                
                                with cols[i]:
                                    st.link_button(f"{label}", gmap_base + query)
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

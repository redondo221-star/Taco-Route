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
    # 安全設定の緩和（エラー回避用）
    safety_settings = {
        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
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

# --- 2. 画面構成 ---
st.title("🚗 Taco-Route")
st.markdown("### プロ仕様・爆速再現モデル")

start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地1", placeholder="例：さいたま市")
with col_v2:
    v2 = st.text_input("任意経由地2", placeholder="")

with st.expander("🔄 詳細設定"):
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

# --- 3. 実行処理 ---
if st.button("🚀 独自の爆速ルートを生成"):
    if not start_point or not destination:
        st.warning("出発地と目的地を入力してください。")
    else:
        prompt = f"""
        あなたは日本の道路マイスターです。以下の条件で3つのルートを提案してください。
        
        【重要ルール】
        1. ルート図の記述様式：
           - 高速道路は必ず `:red[== 道路名・IC名 ==]` と記述。
           - 一般道は必ず `:blue[-- 道路名・バイパス名 --]` と記述。
        2. 案②（爆速コスパ）は、Googleマップの標準ルートを無視し、信号の少ないバイパスと特定のIC区間を組み合わせたプロの最適解を出して。
        3. 最後に必ず以下の地点データ（各案の再現用）を出力すること。
           ※Googleマップで変なルートにならないよう、必ず「〇〇IC入口」「〇〇IC出口」「〇〇バイパス入口」など具体的名称を5つ以上並べること。

        DATA_START
        ROUTE1_POINTS:{start_point},[IC名1],[IC名2],{destination}
        ROUTE2_POINTS:{start_point},[バイパス入口],[IC入口],[IC出口],[バイパス出口],{destination}
        ROUTE3_POINTS:{start_point},[主要経由地1],[主要経由地2],{destination}
        DATA_END
        """

        with st.spinner("AIの遮断を回避しつつ、最短・最安を計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                # エラーチェック
                if not res.candidates or not res.candidates[0].content.parts:
                    st.error("AIの回答が安全フィルターでブロックされました。表現を和らげて再試行します。")
                else:
                    full_text = res.text
                    display_content = full_text.split("DATA_START")[0]
                    
                    # 比較結果の表示
                    st.markdown("---")
                    st.markdown(display_content)

                    # 地図ボタン
                    st.subheader("📍 AI指定のIC・バイパスを強制経由する")
                    cols = st.columns(3)
                    labels = ["①最速", "②爆速コスパ", "③最適"]
                    
                    data_match = re.search(r"DATA_START(.*?)DATA_END", full_text, re.DOTALL)
                    if data_match:
                        data_part = data_match.group(1)
                        for i, label in enumerate(labels):
                            pattern = f"ROUTE{i+1}_POINTS:(.*)"
                            match = re.search(pattern, data_part)
                            if match:
                                pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                                # URL生成（dir=方向指定モードを使用）
                                base_url = "https://www.google.com/maps/dir/"
                                query = "/".join([urllib.parse.quote(p) for p in pts])
                                final_url = base_url + query
                                
                                with cols[i]:
                                    st.link_button(f"{label}を表示", final_url)
            except Exception as e:
                st.error(f"システムエラー: {e}")

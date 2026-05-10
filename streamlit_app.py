import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import urllib.parse
import re

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    try:
        # 404エラー回避のため利用可能なモデルを動的に取得
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if '1.5-flash' in m), 
                     next((m for m in available_models if '1.5-pro' in m), available_models[0]))
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 画面構成 ---
st.title("🚗 Taco-Route")
st.markdown("### 3ルート完全比較・可視化モデル")

start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地1", placeholder="例：さいたま市")
with col_v2:
    v2 = st.text_input("任意経由地2", placeholder="")

with st.expander("🔄 詳細設定"):
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
    input_date = st.date_input("出発日")
    input_time = st.time_input("出発時刻")

# --- 3. 実行処理 ---
if st.button("🚀 独自の爆速ルートを生成"):
    if not start_point or not destination:
        st.warning("出発地と目的地を入力してください。")
    else:
        # プロンプト：URL生成のための「地点抽出」を厳命
        prompt = f"""
        あなたは日本の道路マイスターです。以下の3ルートを提案し、最後にGoogle Map用の詳細地点リストを出力してください。

        【提案内容】
        案①：最速（料金度外視）
        案②：爆速コスパ（あえて高速を降り、流れの良いバイパスを活用して数千円浮かすプロの裏道）
        案③：トータル最適（疲労度とコストのバランス）

        【ルール】
        - ルート図は必ず :red[==高速名==] と :blue[--一般道・バイパス名--] を使い、色分けを明確にすること。
        - 案ごとに「距離・時間・料金」の比較表を出すこと。
        - 案①を基準とした差分（浮いた金額など）を計算すること。

        【重要：MAP地点抽出】
        各ルートをGoogle Mapで強制再現するため、以下の形式で最後に必ず締めてください。
        これがないと地図が正しく表示されません。
        
        DATA_START
        ROUTE1_POINTS:{start_point},[高速の主要地点],{v1 if v1 else ""},{destination}
        ROUTE2_POINTS:{start_point},[爆速コスパのために通るべきバイパス名やIC名1],[バイパス名やIC名2],{v1 if v1 else ""},{destination}
        ROUTE3_POINTS:{start_point},[バランス地点],{v1 if v1 else ""},{destination}
        DATA_END
        """

        with st.spinner("AIが最適なバイパスを探索中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                full_text = res.text

                # 比較表とルート解説の表示
                display_content = full_text.split("DATA_START")[0]
                st.markdown(display_content)

                # 地点データの抽出とボタン生成
                st.subheader("📍 提案ルートを地図で開く")
                st.info("※Googleがルートを勝手に変えないよう、AIが推奨する重要地点を埋め込んでいます。")
                
                cols = st.columns(3)
                labels = ["①最速", "②爆速コスパ", "③最適"]
                
                for i, label in enumerate(labels):
                    pattern = f"ROUTE{i+1}_POINTS:(.*)"
                    match = re.search(pattern, full_text)
                    if match:
                        pts = match.group(1).strip().split(",")
                        # URL生成
                        base_url = "https://www.google.com/maps/dir/"
                        query = "/".join([urllib.parse.quote(p) for p in pts if p])
                        final_url = base_url + query
                        
                        with cols[i]:
                            st.link_button(f"{label}を表示", final_url)

            except Exception as e:
                st.error(f"エラー: {e}")

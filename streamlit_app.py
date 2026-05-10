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
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in available_models if '1.5-flash' in m), 
                     next((m for m in available_models if '1.5-pro' in m), available_models[0]))
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('gemini-1.5-flash')

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
    input_date = st.date_input("出発日")
    input_time = st.time_input("出発時刻")

# --- 3. 実行処理 ---
if st.button("🚀 独自の爆速ルートを生成"):
    if not start_point or not destination:
        st.warning("出発地と目的地を入力してください。")
    else:
        # プロンプトを大幅強化：IC指定と色分けの厳命
        prompt = f"""
        あなたは日本の道路事情とGoogle Mapの仕様を熟知したプロドライバーです。
        以下の3ルートを提案し、最後にGoogle Mapでそのルートを「強制再現」するための地点リストを出力してください。

        【提案ルール】
        1. ルート図の表記（厳守）:
           - 高速道路・有料区間は必ず :red[== 道路名 ==] （赤色）で表記。
           - 一般道・バイパス区間は必ず :blue[-- 道路名 --] （青色）で表記。
        2. 案②「爆速コスパ」は、信号の少ないバイパスを使い、かつ高速の特定区間（例：圏央道のみなど）を組み合わせたプロ推奨の裏道にすること。
        3. 比較表には「距離・時間・料金」を出し、案①との差分を明記すること。

        【重要：MAP再現データ】
        Google Mapが勝手にルートを修正するのを防ぐため、必ず「乗るIC名」「降りるIC名」「経由するバイパス名」を地点として含めてください。
        回答の最後に以下の形式で出力してください。
        
        DATA_START
        ROUTE1_POINTS:{start_point},[乗るIC名],[降りるIC名],{destination}
        ROUTE2_POINTS:{start_point},[バイパス入り口地点],[乗るIC名],[降りるIC名],[バイパス出口地点],{destination}
        ROUTE3_POINTS:{start_point},[主要経由地],{destination}
        DATA_END
        """

        with st.spinner("AIがICの出入り口とバイパスの接続を計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                full_text = res.text

                # 比較表と色分け解説の表示
                display_content = full_text.split("DATA_START")[0]
                st.markdown(display_content)

                # 地点データの抽出と地図ボタンの生成
                st.subheader("📍 AI推奨ルートを地図で再現")
                st.caption("※Google Map上で「AIが指定したIC・バイパス」を経由地に設定しています。")
                
                cols = st.columns(3)
                labels = ["①最速", "②爆速コスパ", "③最適"]
                
                # DATA_START ~ DATA_END の間からデータを抽出
                data_match = re.search(r"DATA_START(.*?)DATA_END", full_text, re.DOTALL)
                if data_match:
                    data_part = data_match.group(1)
                    for i, label in enumerate(labels):
                        pattern = f"ROUTE{i+1}_POINTS:(.*)"
                        match = re.search(pattern, data_part)
                        if match:
                            # 地点を抽出し、URLエンコードして結合
                            pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                            
                            # Google Maps プレイス検索を繋げたURL（経由地を最大化）
                            base_url = "https://www.google.com/maps/dir/"
                            query = "/".join([urllib.parse.quote(p) for p in pts])
                            final_url = base_url + query
                            
                            with cols[i]:
                                st.link_button(f"{label}をMAPで開く", final_url)
                else:
                    st.warning("地図データの生成に失敗しました。もう一度お試しください。")

            except Exception as e:
                st.error(f"エラー: {e}")

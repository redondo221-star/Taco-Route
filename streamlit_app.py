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

# --- 出発日時の設定 ---
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
        # プロンプト：比較表の強制と、JCT名などの不安定な名称を避けるよう指示
        prompt = f"""
        あなたは日本のプロドライバーです。以下の条件で3つのルートを必ず提案してください。

        【条件】
        出発：{start_point} / 目的地：{destination} / 経由：{v1}, {v2} / 出発日時：{full_dt_str}

        【必須回答項目（これがないとやり直しです）】
        1. 案①最速、案②爆速コスパ、案③トータル最適の3案すべてについて、
           「走行距離(km)」「所要時間」「高速料金(円)」を算出した【比較表】（Markdown形式）を冒頭に作成してください。
        2. ルート解説での色分け：
           - 高速・有料道路： :red[== 道路名 (〇〇IC〜××IC) ==] （赤色）
           - 一般道・バイパス： :blue[-- 道路名 --] （青色）
        3. MAP再現用地点データ：
           各案を再現するための地点名を抽出してください。
           注意：JCT名単体などはGoogleマップでエラーになることが多いため、「〇〇IC入口」「〇〇IC出口」のように、必ず実在する施設名やIC名にしてください。

        DATA_START
        ROUTE1_POINTS:{start_point},[IC入口名],[IC出口名],{destination}
        ROUTE2_POINTS:{start_point},[バイパス名],[IC入口名],[IC出口名],{destination}
        ROUTE3_POINTS:{start_point},[主要経由地],{destination}
        DATA_END
        """

        with st.spinner("プロの視点でルートを再計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                if res.candidates:
                    full_text = res.text
                    # DATA_STARTより前の部分（比較表と色分け解説）を確実に表示
                    display_content = full_text.split("DATA_START")[0]
                    
                    st.markdown("---")
                    st.markdown(f"### 🏁 提案結果 ({full_dt_str} 出発)")
                    st.markdown(display_content) # ここに比較表と色分けが含まれます

                    # --- 地図ボタンの生成 ---
                    st.subheader("📍 各ルートをGoogleマップで確認")
                    data_match = re.search(r"DATA_START(.*?)DATA_END", full_text, re.DOTALL)
                    if data_match:
                        data_part = data_match.group(1)
                        cols = st.columns(3)
                        labels = ["①最速ルート", "②爆速コスパ", "③トータル最適"]
                        
                        for i, label in enumerate(labels):
                            pattern = f"ROUTE{i+1}_POINTS:(.*)"
                            match = re.search(pattern, data_part)
                            if match:
                                # 出発点と目的地を、ユーザー入力値で強制上書き（ズレ防止）
                                pts_raw = [p.strip() for p in match.group(1).split(",") if p.strip()]
                                if len(pts_raw) >= 2:
                                    # 抽出された中間地点のみを利用し、最初と最後はユーザー入力を使用
                                    middle_points = pts_raw[1:-1]
                                    final_pts = [start_point] + middle_points + [destination]
                                else:
                                    final_pts = [start_point, destination]
                                
                                # Google Map URL (dir形式)
                                gmap_url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(p) for p in final_pts])
                                
                                with cols[i]:
                                    st.link_button(f"{label}", gmap_url)
                    else:
                        st.error("地図データの生成に失敗しました。")
            except Exception as e:
                st.error(f"エラー: {e}")

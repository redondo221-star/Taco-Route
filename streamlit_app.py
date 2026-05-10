import streamlit as st
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from datetime import datetime
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

start_point = st.text_input("出発地点", placeholder="例：宇都宮駅", key="start")
destination = st.text_input("目的地", placeholder="例：大阪駅", key="dest")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地1", placeholder="例：さいたま市")
with col_v2:
    v2 = st.text_input("任意経由地2", placeholder="")

# --- 出発日時の設定（確実に反映されるよう修正） ---
st.markdown("🕒 **出発日時・詳細設定**")
col_d, col_t = st.columns(2)
with col_d:
    input_date = st.date_input("出発日", value=datetime.now().date())
with col_t:
    input_time = st.time_input("出発時刻", value=datetime.now().time())

vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

# 選択された日時を文字列化
departure_dt = datetime.combine(input_date, input_time)
full_dt_str = departure_dt.strftime('%Y年%m月%d日 %H:%M')

# --- 色付け関数 ---
def apply_custom_colors(text):
    # 高速・有料（赤）
    text = re.sub(r'(高速道路|有料道路|IC|JCT|自動車道|パーキング|==.*?==)', r':red[\1]', text)
    # 一般道・バイパス（青）
    text = re.sub(r'(一般道|国道|県道|バイパス|--.*?--)', r':blue[\1]', text)
    return text

# --- 3. 実行処理 ---
if st.button("🚀 3つのルートを比較・提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地と目的地を入力してください。")
    else:
        # プロンプト：比較表形式の徹底と、データ隠蔽を指示
        prompt = f"""
        あなたは日本のプロドライバーです。以下の条件で3つのルートを提案してください。
        出発：{start_point} / 目的地：{destination} / 経由：{v1}, {v2} / 車種：{vehicle} / 出発日時：{full_dt_str}

        【必須ルール】
        1. 冒頭に必ず以下の【比較表】を作成。
           列：案名 | 距離(km) | 時間 | 料金(円) | 案①との時間差 | 案①との料金差
        2. ルート解説での色分け：
           - 有料・高速は「== 道路名 ==」、一般道は「-- 道路名 --」と表記。
        3. 最後にMAPボタン用の地点リストを DATA_START と DATA_END で囲んで出力。
           ※このリストは後でプログラムで抽出するため、正確なIC名やバイパス名で。

        DATA_START
        ROUTE1_POINTS:{start_point},[IC名],[IC名],{destination}
        ROUTE2_POINTS:{start_point},[バイパス名],[IC名],[バイパス名],{destination}
        ROUTE3_POINTS:{start_point},[主要経由地],{destination}
        DATA_END
        """

        with st.spinner(f"{full_dt_str} 出発のルートを算出中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                if res.candidates:
                    full_text = res.text
                    # 画面表示用（DATA_START以降を切り捨てることで、地点リストを表示させない）
                    display_part = full_text.split("DATA_START")[0]
                    
                    st.markdown("---")
                    st.markdown(f"### 🏁 診断結果 ({full_dt_str} 出発)")
                    
                    # 色付けを適用してメインコンテンツを表示（ここに以前の表が含まれます）
                    st.markdown(apply_custom_colors(display_part))

                    # --- 地図ボタンの生成 ---
                    data_match = re.search(r"DATA_START(.*?)DATA_END", full_text, re.DOTALL)
                    if data_match:
                        st.subheader("📍 各ルートをGoogleマップで開く")
                        data_part = data_match.group(1)
                        cols = st.columns(3)
                        labels = ["①最速", "②爆速コスパ", "③最適"]
                        
                        for i, label in enumerate(labels):
                            pattern = f"ROUTE{i+1}_POINTS:(.*)"
                            match = re.search(pattern, data_part)
                            if match:
                                # 地点を整理（出発地・目的地はユーザー入力を優先）
                                pts_raw = [p.strip() for p in match.group(1).split(",") if p.strip()]
                                middle = pts_raw[1:-1] if len(pts_raw) > 2 else []
                                final_pts = [start_point] + middle + [destination]
                                
                                # Google Map URL
                                gmap_url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(p) for p in final_pts])
                                with cols[i]:
                                    st.link_button(f"{label}を表示", gmap_url)
            except Exception as e:
                st.error(f"エラー: {e}")

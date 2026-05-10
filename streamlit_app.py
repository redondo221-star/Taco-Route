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

start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地1", placeholder="例：さいたま市")
with col_v2:
    v2 = st.text_input("任意経由地2", placeholder="")

# --- 出発日時の設定（確実な時間取得のための修正） ---
st.markdown("🕒 **出発日時・詳細設定**")
col_d, col_t = st.columns(2)
with col_d:
    input_date = st.date_input("出発日", value=datetime.now().date(), key="date_val")
with col_t:
    input_time = st.time_input("出発時刻", value=datetime.now().time(), key="time_val")

vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

# 日時を統合
departure_dt = datetime.combine(input_date, input_time)
full_dt_str = departure_dt.strftime('%Y年%m月%d日 %H:%M')

# --- 強制色付け関数 ---
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
        # プロンプト：以前の比較表形式（差分あり）を徹底指示
        prompt = f"""
        あなたは日本のプロドライバーです。以下の条件で3つのルートを提案してください。
        出発：{start_point} / 目的地：{destination} / 経由：{v1}, {v2} / 車種：{vehicle} / 出発日時：{full_dt_str}

        【回答ルール】
        1. 冒頭に必ず【比較表】を作成してください。
           列構成：案名 | 距離(km) | 時間 | 料金(円) | 案①との時間差 | 案①との料金差
        2. ルート解説での色分け：
           - 有料・高速区間は「== 道路名 (〇〇IC～××IC) ==」と表記。
           - 一般道・バイパス区間は「-- 道路名 --」と表記。
        3. 案①最速、案②爆速コスパ（下道バイパス活用）、案③トータル最適の3案を詳しく解説。
        4. 最後にMAP再現用の地点リストを出力（必ずIC入口・IC出口・バイパス名を含める）。

        DATA_START
        ROUTE1_POINTS:{start_point},[IC入口名],[IC出口名],{destination}
        ROUTE2_POINTS:{start_point},[バイパス入口],[IC入口],[IC出口],[バイパス出口],{destination}
        ROUTE3_POINTS:{start_point},[主要地点],{destination}
        DATA_END
        """

        with st.spinner(f"{full_dt_str} 出発の最適ルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                if res.candidates:
                    full_text = res.text
                    main_part = full_text.split("DATA_START")[0]
                    
                    # --- 色付け適用 ---
                    colored_content = apply_custom_colors(main_part)
                    
                    st.markdown("---")
                    st.markdown(f"### 🏁 診断結果 ({full_dt_str} 出発)")
                    st.markdown(colored_content)

                    # --- 地図ボタンの復活 ---
                    st.subheader("📍 各ルートを一発でMAP表示")
                    data_match = re.search(r"DATA_START(.*?)DATA_END", full_text, re.DOTALL)
                    if data_match:
                        data_part = data_match.group(1)
                        cols = st.columns(3)
                        labels = ["①最速", "②爆速コスパ", "③最適"]
                        
                        for i, label in enumerate(labels):
                            pattern = f"ROUTE{i+1}_POINTS:(.*)"
                            match = re.search(pattern, data_part)
                            if match:
                                pts_raw = [p.strip() for p in match.group(1).split(",") if p.strip()]
                                # 入力値を最初と最後に固定してズレを防止
                                middle = pts_raw[1:-1] if len(pts_raw) > 2 else []
                                final_pts = [start_point] + middle + [destination]
                                
                                # Google Map ルートURL生成
                                gmap_url = "https://www.google.com/maps/dir/" + "/".join([urllib.parse.quote(p) for p in final_pts])
                                with cols[i]:
                                    st.link_button(f"{label}を表示", gmap_url)
            except Exception as e:
                st.error(f"エラー: {e}")

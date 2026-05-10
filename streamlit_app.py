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

st.set_page_config(page_title="Taco-Route", layout="wide")

# --- 2. UI構成 ---
st.title("🚗 Taco-Route")
st.markdown("### 3ルート完全比較・可視化モデル")

with st.sidebar:
    st.header("入力設定")
    start_point = st.text_input("出発地点", value="宇都宮駅")
    destination = st.text_input("目的地", value="大阪駅")
    v1 = st.text_input("必須経由地1", placeholder="例：さいたま市")
    v2 = st.text_input("任意経由地2", placeholder="")
    
    st.markdown("---")
    st.subheader("🕒 出発日時")
    # keyを固定することで値が消えるのを防ぎます
    d = st.date_input("出発日", value=datetime.now().date(), key="date_input")
    t = st.time_input("出発時刻", value=datetime.now().time(), key="time_input")
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

# 統合された日時
departure_dt = datetime.combine(d, t)
dt_str = departure_dt.strftime('%Y-%m-%d %H:%M')

# --- 3. 実行ロジック ---
if st.button("🚀 3つのルートを提案してもらう"):
    if not start_point or not destination:
        st.error("出発地と目的地を入力してください。")
    else:
        # プロンプト：以前の「表が綺麗だった」状態を再現しつつ、MAP用データを隠し持つ
        prompt = f"""
        あなたは日本の交通事情に精通したプロのルートプランナーです。
        出発日時 {dt_str} における、{start_point}から{destination}への3つのルート案を作成してください。

        【必須構成】
        1. 冒頭に比較表をMarkdown形式で作成。
           列：案名 | 距離(km) | 時間 | 料金(円) | 案①との時間差 | 案①との料金差
        
        2. 各案の詳細解説：
           - 高速・有料道路区間は :red[== 道路名 (〇〇IC～××IC) ==] と表記。
           - 一般道・バイパス区間は :blue[-- 道路名 --] と表記。
        
        3. 回答の最後に、地図表示用の地点データのみを以下の形式で出力（ユーザーには見せない隠しデータ）。
           地点は「行ってこい」にならないよう、最小限の主要地点（乗るICと降りるIC等）だけにしてください。

        DATA_START
        ROUTE1:{start_point},[IC名1],[IC名2],{destination}
        ROUTE2:{start_point},[主要バイパス名],[IC名1],[IC名2],{destination}
        ROUTE3:{start_point},[主要経由地],{destination}
        DATA_END
        """

        with st.spinner("プロの視点でルートを解析中..."):
            model = get_working_model()
            response = model.generate_content(prompt)
            
            if response.text:
                full_text = response.text
                
                # 表示用とデータ用に分割
                parts = full_text.split("DATA_START")
                display_content = parts[0]
                
                st.markdown("---")
                st.markdown(f"## 🏁 提案結果 ({dt_str} 出発)")
                
                # メインの表と解説を表示
                st.markdown(display_content)
                
                # --- 地図ボタンの生成 ---
                if "DATA_END" in full_text:
                    data_section = parts[1].split("DATA_END")[0]
                    st.markdown("---")
                    st.subheader("📍 Googleマップでルートを確認")
                    cols = st.columns(3)
                    labels = ["①最速ルート", "②爆速コスパ", "③トータル最適"]
                    
                    for i, label in enumerate(labels):
                        match = re.search(f"ROUTE{i+1}:(.*)", data_section)
                        if match:
                            pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                            # URL生成（Google Maps Directions）
                            # 最初の地点と最後の地点はユーザー入力値を使い、ズレを防止
                            encoded_pts = [urllib.parse.quote(start_point)]
                            for p in pts[1:-1]:
                                encoded_pts.append(urllib.parse.quote(p))
                            encoded_pts.append(urllib.parse.quote(destination))
                            
                            gmap_url = f"https://www.google.com/maps/dir/{'/'.join(encoded_pts)}"
                            with cols[i]:
                                st.link_button(label, gmap_url, use_container_width=True)
            else:
                st.error("AIからの回答が得られませんでした。もう一度お試しください。")

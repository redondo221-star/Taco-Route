import streamlit as st
import datetime
import google.generativeai as genai
import folium
from streamlit_folium import folium_static

# --- 設定 ---
# ※ここにあなたのGemini APIキーを入力してください
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8"
genai.configure(api_key=API_KEY)
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="AIコスパ・タイパ・ナビ", layout="wide")
st.title("🚗 AIルートコンシェルジュ")

# --- 1. 条件入力 ---
with st.sidebar:
    st.header("📋 条件設定")
    origin = st.text_input("出発地点", "宇都宮駅")
    via_point = st.text_input("経由地", "五霞IC")
    destination = st.text_input("目的地", "東京駅")
    
    vehicle = st.radio("車両区分", ["普通車", "軽自動車"], horizontal=True)
    
    dept_type = st.radio("出発時刻", ["今から", "時刻を指定"])
    dept_time = st.time_input("出発時間", datetime.time(8, 0)) if dept_type == "時刻を指定" else "現在"
    
    st.subheader("⚙️ 割引・タイパ設定")
    night_disc = st.checkbox("深夜割引(0-4時)を考慮", value=True)
    holiday_disc = st.checkbox("休日割引(土日祝)を考慮", value=True)
    
    threshold = st.slider("1分短縮にいくら払える？", 0, 100, 30)

# --- 2. AIへのリクエスト ---
if st.button("🚀 最適ルートをAIに尋ねる"):
    prompt = f"""
あなたは日本の道路交通と高速料金（ETC割引含む）の専門家です。
以下の条件で、最もコスパの良いルートを1つ提案してください。

【条件】
出発：{origin} / 経由：{via_point} / 到着：{destination}
車両：{vehicle} / 出発時刻：{dept_time}
時間価値：1分短縮につき{threshold}円まで（これを超える高速利用はNG）
割引：深夜割引={night_disc}, 休日割引={holiday_disc}

【重要】
宇都宮〜五霞間は「新4号バイパス」の利用を強く検討してください。
その上で、どこから高速に乗り、どこで降りるのがベストか判断してください。

【回答形式】
1.【推奨ルート】IC名や道路名を具体的に
2.【料金と時間】想定料金(円)と、下道のみの場合との短縮時間(分)
3.【選定理由】なぜそのルートがベストか（コスパ計算の結果）
4.【地図用】高速区間の開始点と終了点の地名
"""

    with st.spinner("AIが最適な組み合わせを計算しています..."):
        try:
            response = model.generate_content(prompt)
            answer = response.text

            # --- 3. 結果表示 ---
            st.divider()
            
            # 地図の描画（AIの回答に基づいて色分けを模倣）
            st.subheader("🗺️ 提案ルートマップ")
            m = folium.Map(location=[36.0, 139.8], zoom_start=9)
            
            # 本来はAPIでルート座標を取るが、ここでは概念的に表示
            # 高速＝赤、一般道＝青
            st.write("🔴 赤：高速利用区間 / 🔵 青：一般道（新4号など）")
            folium.Marker([36.5, 139.9], tooltip="出発", icon=folium.Icon(color='blue')).add_to(m)
            folium.Marker([35.6, 139.7], tooltip="到着", icon=folium.Icon(color='red')).add_to(m)
            folium_static(m)

            # 選定理由（要約）
            st.success("✅ 最適なルートが見つかりました")
            
            # 詳細表示（ボタンで出し分け）
            tab1, tab2 = st.tabs(["📋 詳細ルート案内", "🧐 なぜこのルート？"])
            
            with tab1:
                st.write(answer.split("3.")[0]) # 理由以外を表示
                
            with tab2:
                if "3." in answer:
                    st.info(answer.split("3.")[1]) # 理由部分を表示
                else:
                    st.write(answer)
                    
        except Exception as e:
            st.error(f"エラーが発生しました: {e}")

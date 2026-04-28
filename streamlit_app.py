import streamlit as st
import datetime
import requests
import google.generativeai as genai
import folium
from streamlit_folium import folium_static

# --- 設定 ---
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY" # Gemini APIキー
genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-pro')

st.set_page_config(page_title="AIルートコンシェルジュ", layout="wide")
st.title("🤖 AIコスパ・タイパ・ナビ")

# --- 1. 入力エリア ---
with st.sidebar:
    st.header("📋 移動条件の設定")
    origin = st.text_input("出発地点", "宇都宮駅")
    via_point = st.text_input("経由地（任意）", "五霞IC")
    destination = st.text_input("目的地", "東京駅")
    
    vehicle_type = st.radio("車両区分", ["普通車", "軽自動車"], horizontal=True)
    
    departure_type = st.radio("出発時刻", ["今から", "時刻を指定"])
    if departure_type == "時刻を指定":
        dept_time = st.time_input("出発希望時刻", datetime.time(8, 0))
    else:
        dept_time = datetime.datetime.now().time()

    st.subheader("⚙️ 割引・タイパ条件")
    st.write("適用する割引")
    night_discount = st.checkbox("深夜割引 (0-4時・30%OFF)", value=True)
    holiday_discount = st.checkbox("休日割引 (土日祝・30%OFF)", value=True)
    
    threshold = st.slider("1分短縮にいくら払える？", 0, 100, 30)

# --- 2. AIへの問い合わせロジック ---
if st.button("🚀 AIに最適ルートを相談する"):
    # AIへのプロンプト作成
    prompt = f"""
あなたは日本の交通事情と高速料金体系に精通したエキスパートです。
以下の条件で、最もコスパとタイパのバランスが良いルートを提案してください。

【移動条件】
・区間：{origin} から {destination} まで（経由地：{via_point}）
・車両：{vehicle_type}
・出発：{dept_time}
・時間価値：1分短縮に{threshold}円まで（これを超えるなら下道優先）
・割引条件：深夜割引={night_discount}、休日割引={holiday_discount}

【特記事項】
・宇都宮〜五霞間は新4号バイパスの利用も検討してください。
・首都高の料金体系（上限・下限）やETC割引を考慮してください。

【回答形式】
以下の3点を必ず含めてください。
1. 推奨ルートの概要（どのICで乗り、どこで降りるか）
2. 予測される合計料金と短縮時間
3. そのルートを選定した詳細な理由（コスパ判定結果）
4. 地図描画用の主要地点の座標（または地名）
"""

    with st.spinner("Geminiが最適なルートを計算中..."):
        response = model.generate_content(prompt)
        ai_result = response.text

    # --- 3. 結果の表示 ---
    st.divider()
    
    # 地図表示（ここではイメージとして簡易表示）
    st.subheader("🗺️ 推奨ルート・マップ")
    m = folium.Map(location=[36.0, 139.8], zoom_start=9)
    # ※本来はAIが返した座標をパースして描画
    # 例：高速＝赤、下道＝青で描画するロジック
    folium.Marker([36.55, 139.90], popup="出発: 宇都宮").add_to(m)
    folium.Marker([35.68, 139.76], popup="到着: 東京").add_to(m)
    folium_static(m)

    # 理由の要約
    st.success(f"💡 AIの選定理由：{ai_result.split('理由')[1][:150]}...")

    # 詳細ボタン
    col_a, col_b = st.columns(2)
    with col_a:
        if st.button("📝 ルートの詳細を見る"):
            st.write(ai_result)
    with col_b:
        if st.button("🧐 なぜこのルート？（詳細理由）"):
            st.info(ai_result.split('理由')[1] if '理由' in ai_result else ai_result)

import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # ご自身のAPIキー

st.set_page_config(page_title="Taco-Route 決定版", layout="wide")

st.sidebar.header("⚖️ あなたのタイパ設定")
threshold = st.sidebar.slider("1分短縮にいくらまで払えますか？", 0, 100, 25)
st.sidebar.info(f"【設定】1分を{threshold}円以下で短縮できるなら高速に乗ります。それ以上なら下道を案内します。")

st.title("🚗 Taco-Route: 高速・下道 乗り分けガイド")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "宇都宮駅")

if 'route_steps' not in st.session_state:
    st.session_state.route_steps = None

def fetch_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.legs.steps"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.route_steps = res['routes'][0]['legs'][0].get('steps', [])
    else:
        st.error("ルート取得に失敗しました。")

if st.button("🚀 最適ルートを算出する"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[35.68, 139.76], zoom_start=8)
    
    st.subheader("📍 運転指示（ここに従って走行してください）")
    
    total_toll = 0
    
    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 高速・有料道路フラグ
        is_highway = any(kw in instr for kw in ["有料区間", "高速", "料金所", "JCT", "IC", "ランプ", "自動車道"])
        # ランプ・接続路フラグ（距離が短い接続路）
        is_ramp = any(kw in instr for kw in ["ランプ", "接続", "入口", "出口", "方面"]) and dist_km < 3.0

        if is_highway:
            # 接続路ではなく本線の場合のみタイパ判定を行う
            if not is_ramp:
                l_time = dist_km * 2.0  # 下道の想定
                h_time = dur_sec / 60   # 高速の想定
                saved = max(0.1, l_time - h_time)
                step_toll = int(dist_km * 25 + 150)
                cost_per_min = step_toll / saved
                
                if cost_per_min <= threshold:
                    color = "blue"
                    total_toll += step_toll
                    st.info(f"✅ 【高速に乗る】 {instr} （{int(saved)}分短縮できるので、乗る価値あり）")
                else:
                    color = "red"
                    st.error(f"⚠️ 【下道へ降りる】 {instr} （1分短縮に{int(cost_per_min)}円もかかるため、降りた方が得です）")
            else:
                # 接続路は「高速」扱いとして描画のみ行う（メッセージは補助的に）
                color = "blue" if 'color' not in locals() or color != "red" else "red"
                st.write(f"  (走行指示: {instr})")
            
            weight = 8
        else:
            # 純粋な一般道
            color = "gray"
            weight = 4
            if dist_km > 0.5:
                st.write(f"▶ {instr} (下道を道なりに進む)")

        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

    folium_static(m)
    st.sidebar.metric("現在のルートでの高速料金", f"{total_toll} 円")

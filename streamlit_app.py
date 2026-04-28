import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # ご自身のAPIキー

st.set_page_config(page_title="Taco-Route 最終修正版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 賢い乗り分けガイド")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京駅")

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

if st.button("🚀 ルートを算出"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[36.56, 139.88], zoom_start=9)
    total_toll = 0
    
    st.subheader("📋 走行ガイド")

    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # A. 有料区間かどうかの判定
        is_paid = "有料区間" in instr
        # B. 入口・出口・ジャンクション等の接続動作かどうかの判定
        is_action = any(kw in instr for kw in ["入る", "出る", "進む", "向かって", "JCT", "IC", "ランプ"])
        # C. 高速本線の走行（ある程度の距離がある有料区間）かどうかの判定
        is_highway_main = is_paid and not is_action and dist_km > 2.0

        color = "gray"
        weight = 4

        if is_paid:
            if is_highway_main:
                # 高速本線でのみタイパ判定（損得勘定）を行う
                l_time = dist_km * 2.0 
                h_time = dur_sec / 60
                saved = max(0.1, l_time - h_time)
                step_toll = int(dist_km * 25 + 150)
                cpm = step_toll / saved
                
                if cpm <= threshold:
                    color = "blue"
                    total_toll += step_toll
                    st.info(f"🔵 【高速を維持】 {instr} ({int(saved)}分短縮 / コスパ良好)")
                else:
                    color = "red"
                    st.error(f"🔴 【高速を降りる推奨】 {instr} (1分短縮に{int(cpm)}円かかるため、下道がお得)")
            else:
                # 入口やJCTなどの「接続動作」
                color = "blue" # 地図上は青で表示
                st.write(f"🛣️ {instr} (高速の分岐・出入り口)")
            weight = 8
        else:
            # 純粋な一般道
            st.write(f"▶ {instr}")

        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

    folium_static(m)
    st.sidebar.metric("推定合計料金", f"{total_toll} 円")

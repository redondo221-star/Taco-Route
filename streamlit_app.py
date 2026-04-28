import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8"

st.set_page_config(page_title="Taco-Route 最適化版", layout="wide")
st.title("🚗 Taco-Route: 中抜きポイント自動発見")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 30)

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京駅")

def fetch_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.legs.steps,routes.polyline"
    }
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE",
        "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 最適ポイントを見つける"):
    res = fetch_route()
    if 'routes' in res:
        steps = res['routes'][0]['legs'][0]['steps']
        m = folium.Map(location=[36.2, 139.8], zoom_start=9)
        total_toll = 0
        
        st.subheader("📍 判定結果")

        for step in steps:
            instr = step.get('navigationInstruction', {}).get('instructions', "道なり")
            dist_km = step.get('distanceMeters', 0) / 1000
            dur_min = int(step.get('staticDuration', "0s").replace("s","")) / 60
            
            # 有料・高速の判定
            is_highway = any(kw in instr for kw in ["有料", "高速", "首都高", "自動車道", "IC", "JCT"])
            
            if is_highway and dist_km > 0:
                # 【重要】ここがシミュレーションロジック
                # 新4号のような快走路（1kmあたり1分）を基準にする
                local_time_est = dist_km * 1.0 
                saved_time = max(0.1, local_time_est - dur_min)
                toll = int(dist_km * 25 + 150)
                cpm = toll / saved_time
                
                # コスパが良い（青）か、悪い（赤）かを1区間ずつ判定
                if cpm <= threshold:
                    color = "blue"
                    total_toll += toll
                    st.info(f"🔵 【高速推奨】 {instr} (短縮効果大: {int(cpm)}円/分)")
                else:
                    color = "red"
                    st.error(f"🔴 【下道（新4号）推奨】 {instr} (コスパ悪: {int(cpm)}円/分)")
                weight = 8
            else:
                color = "gray"
                weight = 4
                if dist_km > 0.5: st.write(f"▶ {instr}")

            if 'polyline' in step:
                pts = polyline.decode(step['polyline']['encodedPolyline'])
                folium.PolyLine(pts, color=color, weight=weight).add_to(m)

        folium_static(m)
        st.sidebar.metric("この設定での合計料金", f"{total_toll} 円")

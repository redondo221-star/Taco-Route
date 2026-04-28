import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8"

st.set_page_config(page_title="Taco-Route 決定版", layout="wide")
st.title("🚗 Taco-Route: あなた専用の最適ルート案内")

# サイドバー設定
threshold = st.sidebar.slider("1分短縮にいくら払える？", 0, 100, 30)

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京駅")

def fetch_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.legs.steps,routes.polyline"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE",
        "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 最適な道を教える"):
    res = fetch_route()
    if 'routes' in res:
        steps = res['routes'][0]['legs'][0]['steps']
        m = folium.Map(location=[36.2, 139.8], zoom_start=9)
        total_toll = 0
        
        st.subheader("📝 本日の走行ルート案内")
        st.write("※コスパを考慮し、最適な区間のみ高速を利用するルートです。")

        # 連続する有料区間をまとめて判定するためのバッファ
        h_buffer = []
        h_dist, h_time = 0, 0

        def process_highway_block(buffer, dist, time):
            """溜まった高速区間を一括で評価し、使うべきなら案内を出す"""
            if not buffer: return 0
            # 短縮時間の計算（新4号基準: 1km=1分）
            saved = max(0.1, dist - time)
            toll = int(dist * 25 + 250) # 入場料＋距離
            cpm = toll / saved
            
            if cpm <= threshold:
                # 【採用】高速として案内
                st.info(f"🔵 【高速利用】 {buffer[0].get('navigationInstruction',{}).get('instructions','高速')} から入る")
                st.write(f"  (約{dist:.1f}km走行 / 料金:{toll}円 / {int(saved)}分短縮)")
                for s in buffer:
                    pts = polyline.decode(s['polyline']['encodedPolyline'])
                    folium.PolyLine(pts, color="blue", weight=8).add_to(m)
                return toll
            else:
                # 【不採用】一般道として描画
                st.write(f"▶️ 【下道（新4号等）推奨】 高速は使わず道なりに進む (約{dist:.1f}km)")
                for s in buffer:
                    pts = polyline.decode(s['polyline']['encodedPolyline'])
                    folium.PolyLine(pts, color="gray", weight=4).add_to(m)
                return 0

        for step in steps:
            instr = step.get('navigationInstruction', {}).get('instructions', "")
            dist_km = step.get('distanceMeters', 0) / 1000
            dur_min = int(step.get('staticDuration', "0s").replace("s","")) / 60
            is_paid = any(kw in instr for kw in ["有料", "高速", "首都高", "IC", "JCT", "入口"])

            if is_paid:
                h_buffer.append(step)
                h_dist += dist_km
                h_time += dur_min
            else:
                # 一般道に切り替わった時に、直前の高速区間をまとめて判定
                if h_buffer:
                    total_toll += process_highway_block(h_buffer, h_dist, h_time)
                    h_buffer, h_dist, h_time = [], 0, 0
                
                # 一般道の案内（重要なもののみ）
                if dist_km > 1.0:
                    st.write(f"▶️ {instr}")
                
                if 'polyline' in step:
                    pts = polyline.decode(step['polyline']['encodedPolyline'])
                    folium.PolyLine(pts, color="gray", weight=4).add_to(m)

        # 最後に残ったバッファを処理
        if h_buffer:
            total_toll += process_highway_block(h_buffer, h_dist, h_time)

        folium_static(m)
        st.sidebar.metric("今回の合計高速料金", f"{total_toll} 円")

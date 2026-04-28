import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # ご自身のAPIキー

st.set_page_config(page_title="Taco-Route 修正版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 中抜き最適化")

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

if st.button("🚀 ルートを検索"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[35.68, 139.76], zoom_start=8)
    
    st.subheader("📑 最適化ルート案内")
    
    total_toll = 0
    in_highway = False # 現在高速に乗っているかどうかのフラグ
    current_highway_color = "blue"

    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 判定1: 明らかに高速・有料道路に関連する語句か
        has_highway_keyword = any(kw in instr for kw in ["有料区間", "高速", "料金所", "JCT", "IC", "ランプ", "自動車道"])
        
        # 判定2: 接続路（ランプ）かどうか
        is_connector = any(kw in instr for kw in ["ランプ", "接続", "入口", "出口", "方面に向かって"]) or dist_km < 1.0

        if has_highway_keyword:
            if not is_connector:
                # 本線でのタイパ計算（ここで色を決める）
                l_time = dist_km * 2.0 
                h_time = dur_sec / 60
                saved = max(0.1, l_time - h_time)
                step_toll = int(dist_km * 25 + 150)
                cpm = step_toll / saved
                
                if cpm <= threshold:
                    current_highway_color = "blue"
                    total_toll += step_toll
                    st.info(f"🔵 {instr} 【高速維持: {step_toll}円 / {int(saved)}分短縮】")
                else:
                    current_highway_color = "red"
                    st.error(f"🔴 {instr} 【★一般道推奨: {int(cpm)}円/分】")
            else:
                # 接続路の場合は、今の高速の色（青か赤）をそのまま使う
                st.write(f"  └ {instr} (高速接続区間)")
            
            color = current_highway_color
            weight = 8
        else:
            # 一般道
            color = "gray"
            weight = 4
            if dist_km > 0.5:
                st.write(f"{instr} (一般道)")

        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

    folium_static(m)
    st.sidebar.metric("推定合計高速代", f"{total_toll} 円")

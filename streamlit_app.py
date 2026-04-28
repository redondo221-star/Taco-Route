import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # ご自身のAPIキー

st.set_page_config(page_title="Taco-Route 決定版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 中抜き最適化（完全版）")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

if 'route_steps' not in st.session_state:
    st.session_state.route_steps = None

def fetch_data():
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

if st.button("🚀 ルートを解析"):
    fetch_data()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[35.68, 139.76], zoom_start=9)
    
    st.subheader(f"📋 ルート分析結果 (基準: {threshold}円/分)")
    
    actual_total_toll = 0
    
    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "直進")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 厳密な高速判定 (Googleの指示文から判定)
        is_highway = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT", "IC", "ランプ"])
        
        # 色とメッセージの初期化
        color = "gray"  # 一般道
        weight = 4
        msg = f"{i+1}. {instr} (一般道走行)"
        
        if is_highway and dist_km > 0:
            # タイパ計算
            l_time = dist_km * 2.0  # 下道の想定(分)
            h_time = dur_sec / 60   # 高速の想定(分)
            saved_min = max(0.1, l_time - h_time)
            
            # 区間料金の計算
            step_toll = int(dist_km * 25 + 150)
            cpm = step_toll / saved_min
            
            if cpm <= threshold:
                color = "blue"  # 高速維持
                weight = 8
                actual_total_toll += step_toll
                msg = f"🔵 {i+1}. {instr} 【高速維持: {step_toll}円 / {int(saved_min)}分短縮】"
            else:
                color = "red"   # 一般道推奨
                weight = 8
                msg = f"🔴 {i+1}. {instr} 【★一般道推奨: コスパ悪({int(cpm)}円/分)】"
        
        # 地図に線を描画
        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]
            
        # 詳細テキスト表示
        if color == "blue":
            st.info(msg)
        elif color == "red":
            st.error(msg)
        else:
            st.write(msg)

    folium_static(m)
    st.sidebar.metric("この設定での合計高速代", f"{actual_total_toll} 円")
    st.sidebar.write("※青色の区間のみの合計料金です")

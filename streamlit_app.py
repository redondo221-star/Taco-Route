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
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.legs.steps"
    }
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.route_steps = res['routes'][0]['legs'][0].get('steps', [])
    else:
        st.error("ルート取得失敗")

if st.button("🚀 ルートを検索・解析"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[35.68, 139.76], zoom_start=8)
    
    total_toll = 0
    st.subheader("📑 最適化ルート案内")

    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_m = step.get('distanceMeters', 0)
        dist_km = dist_m / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 1. 有料道路判定
        is_h = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT", "IC", "ランプ"])
        # 2. 接続路（ランプ）判定：距離が短すぎる場合は「判定対象外（高速の一部）」とする
        is_ramp = any(kw in instr for kw in ["ランプ", "出口", "方面へ向かって"]) and dist_km < 2.0
        
        color = "gray"
        label = "一般道"

        if is_h and dist_km > 0:
            if is_ramp:
                # 接続路は前後の判定に従う（基本は青）
                color = "blue"
                st.write(f"  └ {instr} (高速接続路)")
            else:
                # 本線のタイパ計算
                l_time = dist_km * 2.0  # 下道(分)
                h_time = dur_sec / 60   # 高速(分)
                saved = max(0.1, l_time - h_time)
                toll = int(dist_km * 25 + 150)
                cpm = toll / saved
                
                if cpm <= threshold:
                    color = "blue"
                    total_toll += toll
                    st.info(f"🔵 {instr} 【高速維持: {toll}円 / {int(saved)}分短縮】")
                else:
                    color = "red"
                    st.error(f"🔴 {instr} 【★一般道推奨: {int(cpm)}円/分】")
        else:
            if dist_km > 0.5:
                st.write(f"  {instr} (一般道)")

        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=8 if color != "gray" else 4, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

    folium_static(m)
    st.sidebar.metric("推定合計高速代", f"{total_toll} 円")

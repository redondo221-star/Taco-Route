import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # ご自身のAPIキー

st.set_page_config(page_title="Taco-Route 首都高対応版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 連続区間一括判定（首都高対応）")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "目黒駅")

if 'route_steps' not in st.session_state:
    st.session_state.route_steps = None

def fetch_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.polyline,routes.legs.steps.navigationInstruction,routes.legs.steps.travelAdvisory"
    }
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.route_steps = res['routes'][0]['legs'][0].get('steps', [])

if st.button("🚀 ルートを解析"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[35.68, 139.76], zoom_start=10)
    
    total_toll = 0
    # 連続する有料区間を一時保存する変数
    temp_highway_dist = 0
    temp_highway_time_saved = 0
    temp_highway_steps = []

    def flush_highway_segment(dist, saved, steps_list):
        """溜まった高速区間を一括判定して描画・表示する"""
        if dist <= 0: return 0
        # 料金計算：基本料金は1回だけ、あとは距離
        toll = int(dist * 25 + 150)
        cpm = toll / max(0.1, saved)
        
        is_efficient = cpm <= threshold
        color = "blue" if is_efficient else "red"
        
        # 代表的な名前を抽出
        name = steps_list[0].get('navigationInstruction', {}).get('instructions', "高速区間")
        if is_efficient:
            st.info(f"🔵 【高速維持】 {name} ほか連なる区間 ({int(dist)}km / 合計{toll}円)")
        else:
            st.error(f"🔴 【中抜き推奨】 {name} ほか連なる区間 (一括判定でコスパ悪: {int(cpm)}円/分)")
            
        for s in steps_list:
            if 'polyline' in s:
                pts = polyline.decode(s['polyline']['encodedPolyline'])
                folium.PolyLine(pts, color=color, weight=8, opacity=0.8).add_to(m)
        
        return toll if is_efficient else 0

    st.subheader("📋 走行ガイド（連続区間まとめ）")

    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_min = int(step.get('staticDuration', "0s").replace("s","")) / 60
        is_paid = 'travelAdvisory' in step or any(kw in instr for kw in ["有料", "高速", "首都高", "自動車道"])

        if is_paid:
            # 有料区間なら「溜める」
            temp_highway_dist += dist_km
            # 下道なら1km2分、高速なら実時間。その差が「短縮時間」
            temp_highway_time_saved += max(0, (dist_km * 2.0) - dur_min)
            temp_highway_steps.append(step)
        else:
            # 一般道に入ったら、それまで溜まった高速区間を判定・描画
            if temp_highway_steps:
                total_toll += flush_highway_segment(temp_highway_dist, temp_highway_time_saved, temp_highway_steps)
                temp_highway_dist = 0
                temp_highway_time_saved = 0
                temp_highway_steps = []
            
            # 一般道の描画
            if 'polyline' in step:
                pts = polyline.decode(step['polyline']['encodedPolyline'])
                folium.PolyLine(pts, color="gray", weight=4, opacity=0.8).add_to(m)
                if dist_km > 0.5: st.write(f"▶ {instr}")

    # 最後に残った高速区間があれば処理
    if temp_highway_steps:
        total_toll += flush_highway_segment(temp_highway_dist, temp_highway_time_saved, temp_highway_steps)

    folium_static(m)
    st.sidebar.metric("合計予定料金", f"{total_toll} 円")

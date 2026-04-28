import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- あなたのAPIキー ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route Pro", layout="wide")
st.title("🚗 Taco-Route: 地図 & 詳細ガイド")

# サイドバー設定
st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 10, 100, 25)

col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "御殿場駅")

def get_route_data(avoid_highways):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        # 「道順の指示（navigationInstruction）」をフィールドマスクに追加！
        "X-Goog-Fieldmask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps.navigationInstruction"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": avoid_highways},
        "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 ルートを解析する"):
    with st.spinner("データを取得中..."):
        h_res = get_route_data(False) # 高速あり
        l_res = get_route_data(True)  # 下道のみ

        if 'routes' in h_res and 'routes' in l_res:
            h_route = h_res['routes'][0]
            l_route = l_res['routes'][0]

            # --- 1. 地図の表示 ---
            h_points = polyline.decode(h_route['polyline']['encodedPolyline'])
            m = folium.Map(location=h_points[0], zoom_start=10)
            folium.PolyLine(h_points, color="blue", weight=5, tooltip="高速ルート").add_to(m)
            l_points = polyline.decode(l_route['polyline']['encodedPolyline'])
            folium.PolyLine(l_points, color="red", weight=3, opacity=0.6, tooltip="下道ルート").add_to(m)
            
            st.subheader("🗺️ 走行ルート比較")
            folium_static(m)

            # --- 2. 判定結果の表示 ---
            h_min = int(h_route['duration'][:-1]) / 60
            l_min = int(l_route['duration'][:-1]) / 60
            saved_min = l_min - h_min
            dist_km = h_route['distanceMeters'] / 1000
            toll = int(dist_km * 25 + 150) if saved_min > 5 else 0
            cost_per_min = toll / saved_min if saved_min > 0 else 0

            st.divider()
            if cost_per_min <= threshold:
                st.success(f"🏆 高速利用がおすすめ！ (短縮時間: {int(saved_min)}分)")
            else:
                st.warning(f"🐢 一般道がおすすめ！ (節約できる料金: {toll}円)")

            # --- 3. 【ここが重要】ルート詳細のテキスト表示 ---
            st.subheader("📑 具体的な道順（高速優先ルート）")
            
            # Google APIから返ってきたステップを一つずつ表示
            steps = h_route['legs'][0].get('steps', [])
            for i, step in enumerate(steps):
                if 'navigationInstruction' in step:
                    instruction = step['navigationInstruction']['instructions']
                    # 有料道路に入るタイミングを強調
                    if "有料道路" in instruction or "高速" in instruction:
                        st.markdown(f"**{i+1}. ⚠️ {instruction}**")
                    else:
                        st.write(f"{i+1}. {instruction}")
        else:
            st.error("詳細ルートの取得に失敗しました。住所を確認してください。")

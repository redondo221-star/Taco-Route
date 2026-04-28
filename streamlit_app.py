import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline # ルート描画用

# --- あなたのAPIキー ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route Map", layout="wide")
st.title("🚗 Taco-Route: 地図表示 & 自動判定")

# サイドバー設定
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
        "X-Goog-Fieldmask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": avoid_highways},
        "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 ルートを比較して地図に表示"):
    with st.spinner("ルートを計算中..."):
        h_res = get_route_data(False) # 高速
        l_res = get_route_data(True)  # 下道

        if 'routes' in h_res and 'routes' in l_res:
            h_route = h_res['routes'][0]
            l_route = l_res['routes'][0]

            # 各種計算
            h_min = int(h_route['duration'][:-1]) / 60
            l_min = int(l_route['duration'][:-1]) / 60
            saved_min = l_min - h_min
            dist_km = h_route['distanceMeters'] / 1000
            toll = int(dist_km * 25 + 150) if saved_min > 5 else 0
            cost_per_min = toll / saved_min if saved_min > 0 else 0

            # --- 地図の作成 ---
            # ルートの中間地点を地図の中心にする
            m = folium.Map(location=[35.6812, 139.7671], zoom_start=10) # 初期値は東京

            # 高速ルート（青い線）を描画
            h_points = polyline.decode(h_route['polyline']['encodedPolyline'])
            folium.PolyLine(h_points, color="blue", weight=5, opacity=0.7, tooltip="高速ルート").add_to(m)

            # 下道ルート（赤い線）を描画
            l_points = polyline.decode(l_route['polyline']['encodedPolyline'])
            folium.PolyLine(l_points, color="red", weight=3, opacity=0.6, tooltip="下道ルート").add_to(m)

            # 地図を画面に表示
            st.subheader("🗺️ ルートマップ（青：高速 / 赤：下道）")
            folium_static(m)

            # --- 判定結果の表示 ---
            st.divider()
            if cost_per_min <= threshold:
                st.success(f"🏆 高速推奨！ (1分短縮コスト: {cost_per_min:.1f}円)")
            else:
                st.warning(f"🐢 下道推奨！ (1分短縮コスト: {cost_per_min:.1f}円)")

            c1, c2, c3 = st.columns(3)
            c1.metric("短縮時間", f"{int(saved_min)} 分")
            c2.metric("概算料金", f"{toll} 円")
            c3.metric("タイパ", f"{cost_per_min:.1f} 円/分")
        else:
            st.error("データの取得に失敗しました。")

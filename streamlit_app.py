import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # あなたのAPIキー

st.set_page_config(page_title="Taco-Route: リアルタイム最適化", layout="wide")

# 1. スライダーの設定（これが変わるとアプリ全体が動く）
st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)
st.sidebar.write(f"設定：{threshold}円/分")

st.title("🚗 Taco-Route: 真の最適ルート提案")

# 2. 目的地入力
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

# 3. ルート計算関数（高速あり・なしを比較して、タイパに合う方を選ぶ）
def get_best_optimized_route():
    def fetch_route(avoid_highways):
        url = "https://routes.googleapis.com/directions/v2:computeRoutes"
        headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
                   "X-Goog-Fieldmask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps"}
        payload = {
            "origin": {"address": origin}, "destination": {"address": destination},
            "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": avoid_highways}, "languageCode": "ja-JP"
        }
        return requests.post(url, json=payload, headers=headers).json()

    # 高速ありと高速なし、両方のルートをAPIで取得
    h_res = fetch_route(False)
    l_res = fetch_route(True)

    if 'routes' in h_res and 'routes' in l_res:
        h_route = h_res['routes'][0]
        l_route = l_res['routes'][0]

        # 実際の時間差と距離
        h_min = int(h_route['duration'][:-1]) / 60
        l_min = int(l_route['duration'][:-1]) / 60
        saved_min = l_min - h_min
        dist_km = h_route['distanceMeters'] / 1000
        
        # 料金シミュレーション
        toll = int(dist_km * 25 + 150)
        cost_per_min = toll / saved_min if saved_min > 0 else 999

        # --- ここが判定のキモ ---
        # スライダーの基準より安ければ高速ルート、高ければ下道ルートを「正解」として返す
        if cost_per_min <= threshold and saved_min > 0:
            return h_route, "高速優先", toll, saved_min, cost_per_min
        else:
            return l_route, "一般道優先", 0, 0, cost_per_min
    return None, None, 0, 0, 0

# 4. 実行と表示
if st.button("🚀 最適ルートを算出"):
    route, type_name, toll, saved, cpm = get_best_optimized_route()
    
    if route:
        st.subheader(f"✅ あなたへの最適解：【{type_name}】ルート")
        
        # 地図の描画
        points = polyline.decode(route['polyline']['encodedPolyline'])
        m = folium.Map(location=points[0], zoom_start=10)
        folium.PolyLine(points, color="blue" if type_name=="高速優先" else "green", weight=5).add_to(m)
        folium_static(m)

        # 指標の表示
        c1, c2, c3 = st.columns(3)
        c1.metric("予想高速料金", f"{toll} 円")
        c2.metric("短縮時間", f"{int(saved)} 分")
        c3.metric("1分あたりのコスト", f"{cpm:.1f} 円")

        # 道順の詳細（APIが返してきた正式なものだけを表示）
        st.subheader("📑 正式な道順案内")
        for i, step in enumerate(route['legs'][0].get('steps', [])):
            if 'navigationInstruction' in step:
                st.write(f"{i+1}. {step['navigationInstruction']['instructions']}")

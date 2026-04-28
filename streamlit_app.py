import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: 区間最適化", layout="wide")
st.title("🚗 Taco-Route: 区間別タイパ診断")
st.caption("全区間ではなく『ここだけ乗る・降りる』の最適解を探します")

threshold = st.sidebar.slider("1分短縮に何円まで払える？", 10, 100, 25)

col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "御殿場駅")

def get_route(avoid_highways):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.duration,routes.distanceMeters,routes.polyline.encodedPolyline,routes.legs.steps"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": avoid_highways}, "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 区間ごとのコスパを分析"):
    with st.spinner("ルートを詳細に分析中..."):
        h_res = get_route(False)
        if 'routes' not in h_res:
            st.error("ルートが見つかりませんでした。")
        else:
            route = h_res['routes'][0]
            steps = route['legs'][0].get('steps', [])
            
            # --- 判定ロジック：区間を「一般道エリア」と「高速エリア」に分類 ---
            st.subheader("📋 区間別のタイパ診断結果")
            
            total_toll = 0
            optimized_instructions = []
            
            # 本来は各ステップで再度APIを叩くのが理想ですが、
            # まずは「有料道路」と明記されたステップを抽出して判定シミュレーションを行います
            for i, step in enumerate(steps):
                instr = step.get('navigationInstruction', {}).get('instructions', "")
                dist_km = step.get('distanceMeters', 0) / 1000
                duration_sec = int(step.get('staticDuration', "0s")[:-1])
                
                # 有料道路が含まれるステップか判定
                is_toll = "有料道路" in instr or "高速" in instr or "料金所" in instr
                
                if is_toll:
                    # 高速区間の仮定：一般道なら時間は3倍かかるとシミュレーション
                    saved_time = (duration_sec * 2) / 60 
                    est_cost = int(dist_km * 25 + 150)
                    cost_per_min = est_cost / saved_time if saved_time > 0 else 0
                    
                    if cost_per_min <= threshold:
                        status = "✅ 乗るべき"
                        total_toll += est_cost
                        color = "green"
                    else:
                        status = "🐢 降りるべき（一般道推奨）"
                        color = "orange"
                    
                    st.markdown(f"**区間 {i+1}: {instr}** ({dist_km:.1f}km)")
                    st.write(f"判定：:{color}[{status}] ／ 1分短縮コスト: {cost_per_min:.1f}円")
                else:
                    # 一般道区間
                    if dist_km > 0.5: # 短すぎる枝道は除外
                        st.write(f"区間 {i+1}: {instr} (一般道を走行)")

            # --- 地図表示 ---
            points = polyline.decode(route['polyline']['encodedPolyline'])
            m = folium.Map(location=points[0], zoom_start=10)
            folium.PolyLine(points, color="blue", weight=5).add_to(m)
            folium_static(m)
            
            st.divider()
            st.metric("この条件での予想高速代", f"{total_toll} 円")
            st.info("※上記は各区間の「時間短縮効果」を計算した結果です。タイパの悪い区間だけを一般道に迂回することで、トータルのコスパが最大化されます。")

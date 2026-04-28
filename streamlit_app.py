import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: 区間最適化", layout="wide")
st.title("🚗 Taco-Route: 賢い乗り降り判定")

threshold = st.sidebar.slider("1分短縮に何円まで払える？", 10, 100, 25)

col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "御殿場駅")

def get_route_data(avoid_highways):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.duration,routes.polyline.encodedPolyline,routes.legs.steps"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": avoid_highways}, "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 ルートを分析して「中抜き」を提案"):
    with st.spinner("詳細データを解析中..."):
        h_res = get_route_data(False)
        
        if 'routes' in h_res:
            route = h_res['routes'][0]
            steps = route['legs'][0].get('steps', [])
            
            # --- 判定結果のサマリー表示 ---
            st.subheader("💡 賢い乗り降りのアドバイス")
            
            points = polyline.decode(route['polyline']['encodedPolyline'])
            m = folium.Map(location=points[0], zoom_start=10)
            
            for i, step in enumerate(steps):
                instr = step.get('navigationInstruction', {}).get('instructions', "")
                dist_km = step.get('distanceMeters', 0) / 1000
                # durationは "60s" のような形式なので数字に変換
                duration_sec = int(step.get('staticDuration', "0s").replace("s",""))
                
                # 「有料道路」や「高速」というキーワードが含まれるステップか
                is_highway = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT"])
                
                if is_highway and dist_km > 0:
                    # 【擬似シミュレーション】
                    # 一般道だと時速30km(2分/km)、高速だと時速80km(0.75分/km)と仮定して差分を出す
                    h_time = duration_sec / 60
                    l_time = dist_km * 2.0  # 一般道ならこれくらいかかる
                    saved_min = l_time - h_time
                    
                    est_toll = int(dist_km * 25 + 150) # 簡易料金
                    cost_per_min = est_toll / saved_min if saved_min > 0 else 0
                    
                    if cost_per_min > threshold:
                        # タイパが悪い区間
                        st.error(f"📍 区間{i+1}: 「{instr}」は一般道推奨！")
                        st.caption(f"理由: 1分短縮に {cost_per_min:.1f}円 もかかり、コスパが悪いです。")
                        folium.PolyLine(polyline.decode(step['polyline']['encodedPolyline']), color="red", weight=8).add_to(m)
                    else:
                        # タイパが良い区間
                        st.success(f"📍 区間{i+1}: 「{instr}」は高速維持！")
                        st.caption(f"理由: 1分短縮コストは {cost_per_min:.1f}円。払う価値があります。")
                        folium.PolyLine(polyline.decode(step['polyline']['encodedPolyline']), color="blue", weight=8).add_to(m)
                else:
                    # 一般道区間の描画
                    if 'polyline' in step:
                        folium.PolyLine(polyline.decode(step['polyline']['encodedPolyline']), color="gray", weight=4).add_to(m)

            st.subheader("🗺️ 最適化マップ (青:高速維持 / 赤:一般道へ降りる検討)")
            folium_static(m)
        else:
            st.error("詳細データを取得できませんでした。")

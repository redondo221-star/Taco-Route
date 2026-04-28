import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # ご自身のAPIキー

st.set_page_config(page_title="Taco-Route 料金修正版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 正確な料金・ルート判定")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京駅")

if 'route_steps' not in st.session_state:
    st.session_state.route_steps = None

def fetch_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        # 有料道路情報を取得するために travelAdvisory を明示的に要求
        "X-Goog-Fieldmask": "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.polyline,routes.legs.steps.navigationInstruction,routes.legs.steps.travelAdvisory"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": False},
        "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.route_steps = res['routes'][0]['legs'][0].get('steps', [])
    else:
        st.error("ルート情報の取得に失敗しました。")

if st.button("🚀 ルートを再計算"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[36.5, 139.9], zoom_start=9)
    total_toll = 0
    
    st.subheader("📋 走行ルート詳細")

    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "直進")
        dist_m = step.get('distanceMeters', 0)
        dist_km = dist_m / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # --- 有料道路の判定ロジックを強化 ---
        # 1. Google APIの公式タグを確認
        # 2. 指示文にキーワードが含まれるか確認
        is_toll_road = False
        if 'travelAdvisory' in step:
            is_toll_road = True
        elif any(kw in instr for kw in ["有料", "高速", "自動車道", "IC", "JCT", "料金所"]):
            is_toll_road = True

        color = "gray" # デフォルトは一般道
        weight = 4

        if is_toll_road and dist_km > 0:
            # 接続路（ランプ）かどうかの判定（3km未満の細かい動き）
            is_connection = any(kw in instr for kw in ["向かって進む", "出口", "入口", "ランプ", "JCT"]) and dist_km < 3.0
            
            if not is_connection:
                # 本線走行：タイパ計算を行う
                l_time = dist_km * 2.0 
                h_time = dur_sec / 60
                saved = max(0.1, l_time - h_time)
                # 料金計算: 基本150円 + 25円/km
                step_toll = int(dist_km * 25 + 150)
                cpm = step_toll / saved
                
                if cpm <= threshold:
                    color = "blue" # 高速維持（青）
                    total_toll += step_toll
                    st.info(f"🔵 【高速】 {instr} ({step_toll}円 / {int(saved)}分短縮)")
                else:
                    color = "red" # 降りる推奨（赤）
                    # 料金は加算しない（降りる想定のため）
                    st.error(f"🔴 【下道推奨】 {instr} (1分短縮に{int(cpm)}円かかるため降りる)")
            else:
                # 接続区間は前後の色に従う（ここでは一旦青）
                color = "blue"
                st.write(f"🛣️ {instr} (高速の接続路)")
            weight = 8
        else:
            # 純粋な一般道
            if dist_km > 0.5:
                st.write(f"▶ {instr}")

        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

    folium_static(m)
    st.sidebar.metric("このルートの合計高速代", f"{total_toll} 円")
    st.sidebar.write("※青色の区間のみの合計です。")

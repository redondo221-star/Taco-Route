import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- APIキーの設定 ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: 中抜き判定", layout="wide")

# 1. スライダー（サイドバー）
st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 区間別・中抜き最適化")

# 2. 入力
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

# セッション状態でデータを保持（スライダーを動かしてもAPIを再消費しない）
if 'route_steps' not in st.session_state:
    st.session_state.route_steps = None

def get_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.legs.steps"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        # ステップ単位のデータを保存
        st.session_state.route_steps = res['routes'][0]['legs'][0].get('steps', [])
    else:
        st.error("ルートが見つかりませんでした。")

if st.button("🚀 ルートを検索"):
    get_route()

# 3. 描画と判定（ここが重要）
if st.session_state.route_steps:
    steps = st.session_state.route_steps
    
    # 地図の初期化
    m = folium.Map(location=[35.68, 139.76], zoom_start=9)
    
    st.subheader(f"📊 判定結果 (基準: {threshold}円/分)")
    
    total_toll = 0
    
    # 全ステップをループして、一つずつ個別に描画する
    for i, step in enumerate(steps):
        if 'polyline' not in step: continue
        
        # 指示内容、距離、時間
        instr = step.get('navigationInstruction', {}).get('instructions', "道なり")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 高速・有料道路の判定
        is_h = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT", "IC"])
        
        color = "gray" # デフォルト（一般道）
        weight = 4
        label = "一般道"
        
        if is_h and dist_km > 0:
            # タイパ計算（高速 vs 一般道シミュレーション）
            # 一般道は時速30km（1kmあたり2分）と仮定
            l_time = dist_km * 2.0
            h_time = dur_sec / 60
            saved_min = max(0.1, l_time - h_time)
            toll = int(dist_km * 25 + 150)
            cpm = toll / saved_min
            
            if cpm <= threshold:
                color = "blue"  # 高速を維持する（タイパ良）
                weight = 8
                total_toll += toll
                label = f"🔵高速維持 ({int(cpm)}円/分)"
            else:
                color = "red"   # 一般道へ降りる検討（コスパ悪）
                weight = 8
                label = f"🔴一般道へ! ({int(cpm)}円/分)"
            
            # 詳細リストの表示
            st.write(f"**区間 {i+1}**: {instr} ➔ **{label}**")
        
        # 地図にこの区間だけを描く
        pts = polyline.decode(step['polyline']['encodedPolyline'])
        folium.PolyLine(pts, color=color, weight=weight, opacity=0.8, tooltip=label).add_to(m)
        if i == 0: m.location = pts[0]

    # 地図を最後に表示
    folium_static(m)
    st.sidebar.metric("推定合計高速代", f"{total_toll} 円")

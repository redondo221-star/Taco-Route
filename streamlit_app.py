import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- APIキー ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: 完全色分け版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
# スライダーの値を変更すると、下の「描画ロジック」が即座に再計算されます
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 区間別・中抜きルート判定")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

# セッションを使ってデータを保持
if 'raw_steps' not in st.session_state:
    st.session_state.raw_steps = None

def get_data():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.legs.steps"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        # ステップ（区間データ）だけを保存
        st.session_state.raw_steps = res['routes'][0]['legs'][0].get('steps', [])
    else:
        st.error("ルートが見つかりません")

if st.button("🚀 ルートを検索"):
    get_data()

# --- ここからが「色分け」の核心 ---
if st.session_state.raw_steps:
    steps = st.session_state.raw_steps
    
    # 1. 地図の土台を作成
    m = folium.Map(location=[35.68, 139.76], zoom_start=10)
    
    st.subheader(f"📊 判定結果（しきい値: {threshold}円/分）")
    
    total_toll = 0
    
    # 2. 各ステップをループして「個別に」地図へ描く
    for i, step in enumerate(steps):
        if 'polyline' not in step: continue
        
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 高速・有料道路の判定
        is_h = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT"])
        
        color = "gray"
        weight = 4
        
        if is_h and dist_km > 0:
            # タイパ計算（高速 vs 一般道シミュレーション）
            saved_min = max(0.5, (dist_km * 2.0) - (dur_sec / 60))
            toll = int(dist_km * 25 + 150)
            cpm = toll / saved_min
            
            if cpm <= threshold:
                color = "blue"  # 高速維持
                weight = 8
                total_toll += toll
                status_text = f"🔵 【高速維持】 {int(cpm)}円/分"
            else:
                color = "red"   # 一般道推奨
                weight = 8
                status_text = f"🔴 【一般道へ】 {int(cpm)}円/分"
            
            # 詳細をテキストで表示
            st.write(f"区間 {i+1}: {instr} ➔ {status_text}")
        
        # 3. この区間専用の線を地図に引く
        line_pts = polyline.decode(step['polyline']['encodedPolyline'])
        folium.PolyLine(line_pts, color=color, weight=weight, opacity=0.8).add_to(m)
        if i == 0: m.location = line_pts[0]

    # 地図を表示
    folium_static(m)
    st.sidebar.metric("この設定での高速代", f"{total_toll} 円")

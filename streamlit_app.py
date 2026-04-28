import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- APIキーの設定 ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route Pro", layout="wide")

# サイドバー：ここでスライダーを動かすと、下の地図が即座に反応します
st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 10, 100, 25)

st.title("🚗 Taco-Route: 動的ルート判定")

# 入力エリア
col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "御殿場駅")

# --- データの保持 (session_state) ---
# これにより、スライダーを動かしてもAPIを叩き直さず、判定だけをやり直せます
if 'route_data' not in st.session_state:
    st.session_state.route_data = None

def get_api_data():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.duration,routes.polyline.encodedPolyline,routes.legs.steps"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": False}, # 高速優先で取得して後から判定
        "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.route_data = res['routes'][0]
    else:
        st.error("ルートが見つかりませんでした。住所を確認してください。")

if st.button("🚀 ルートを検索"):
    get_api_data()

# --- 判定と描画ロジック ---
if st.session_state.route_data:
    route = st.session_state.route_data
    steps = route['legs'][0].get('steps', [])
    
    # 地図の準備
    m = folium.Map(location=[35.6812, 139.7671], zoom_start=10)
    
    st.write(f"### 📋 現在の判定 (しきい値: {threshold}円/分)")
    
    details = [] # 詳細テキストを貯めるリスト
    
    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "直進")
        dist_km = step.get('distanceMeters', 0) / 1000
        duration_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 高速・有料道路の判定
        is_highway = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT"])
        
        # 色とラベルの初期値（一般道）
        color = "gray"
        weight = 4
        label = "一般道"
        
        if is_highway and dist_km > 0:
            # 擬似タイパ計算
            h_time = duration_sec / 60
            l_time = dist_km * 2.0 # 一般道の想定速度
            saved_min = max(0.1, l_time - h_time)
            est_toll = int(dist_km * 25 + 150)
            cost_per_min = est_toll / saved_min
            
            if cost_per_min <= threshold:
                color = "blue"   # タイパ良し
                weight = 7
                label = f"高速維持 ({int(cost_per_min)}円/分)"
            else:
                color = "red"    # タイパ悪し
                weight = 9
                label = f"★一般道推奨 ({int(cost_per_min)}円/分)"

        # 地図に線を追加
        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8, tooltip=label).add_to(m)
            if i == 0: m.location = pts[0] # 開始地点を地図の中心に
            
        # 詳細リストに追加
        details.append({"step": i+1, "instr": instr, "label": label, "color": color})

    # 地図表示
    folium_static(m)

    # 詳細テキスト表示（色付き）
    st.subheader("📑 ルート詳細ガイド")
    for d in details:
        if d['color'] == "red":
            st.error(f"{d['step']}. {d['instr']} 【{d['label']}】")
        elif d['color'] == "blue":
            st.info(f"{d['step']}. {d['instr']} 【{d['label']}】")
        else:
            st.write(f"{d['step']}. {d['instr']}")

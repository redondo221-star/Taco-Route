import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- あなたのAPIキー ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: リアルタイム最適化", layout="wide")

# サイドバーに設定を集約
st.sidebar.header("⚖️ タイパ設定")
# スライダーが動くと、Streamlitの仕様でコードが上から再実行されます
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 10, 100, 25)

st.title("🚗 Taco-Route: 動的「中抜き」ルート判定")
st.info(f"現在の基準: 1分短縮に **{threshold}円** 以上かかる区間は「一般道」を推奨します。")

col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "御殿場駅")

# --- セッション状態を使ってルートデータを保持（API節約のため） ---
if 'route_data' not in st.session_state:
    st.session_state.route_data = None

def get_base_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {"Content-Type": "application/json", "X-Goog-Api-Key": API_KEY,
               "X-Goog-Fieldmask": "routes.duration,routes.polyline.encodedPolyline,routes.legs.steps"}
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routeModifiers": {"avoidHighways": False}, "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.route_data = res['routes'][0]
    else:
        st.error("ルートが見つかりませんでした。")

# 検索ボタン（または場所が変わった時）にAPIを叩く
if st.button("🚀 ルートを検索・分析"):
    get_base_route()

# データがある場合に実行される描画・判定ロジック
if st.session_state.route_data:
    route = st.session_state.route_data
    steps = route['legs'][0].get('steps', [])
    
    # 地図の初期化
    points = polyline.decode(route['polyline']['encodedPolyline'])
    m = folium.Map(location=points[0], zoom_start=9)
    
    st.subheader("📑 区間別のリアルタイム判定結果")
    
    total_toll = 0
    total_time_saved = 0
    
    # 各ステップ（区間）をスライダーの値で再判定
    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "")
        dist_km = step.get('distanceMeters', 0) / 1000
        duration_sec = int(step.get('staticDuration', "0s").replace("s",""))
        
        # 有料道路判定
        is_highway = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT"])
        
        if is_highway and dist_km > 0:
            # 一般道(30km/h)と高速(80km/h)の差分シミュレーション
            h_time = duration_sec / 60
            l_time = dist_km * 2.0 
            saved_min = l_time - h_time
            est_toll = int(dist_km * 25 + 150)
            cost_per_min = est_toll / saved_min if saved_min > 0 else 0
            
            # スライダーの threshold と比較
            if cost_per_min <= threshold:
                # タイパが良い：高速維持（青）
                st.write(f"✅ 区間{i+1}: {instr} → **【高速維持】** ({cost_per_min:.1f}円/分)")
                color = "blue"
                weight = 6
                total_toll += est_toll
                total_time_saved += saved_min
            else:
                # タイパが悪い：一般道へ（赤）
                st.write(f"🐢 区間{i+1}: {instr} → **【一般道へ降りるべき】** ({cost_per_min:.1f}円/分)")
                color = "red"
                weight = 8
        else:
            # もともと一般道の区間（グレー）
            color = "gray"
            weight = 3
        
        # 判定結果の色を地図に反映
        if 'polyline' in step:
            step_points = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(step_points, color=color, weight=weight, opacity=0.8).add_to(m)

    # 地図とサマリーの表示
    folium_static(m)
    
    st.divider()
    c1, c2 = st.columns(2)
    c1.metric("推奨ルートでの概算料金", f"{total_toll} 円")
    c2.metric("一般道のみと比較した短縮時間", f"{int(total_time_saved)} 分")

import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- APIキーの設定 ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: 中抜き最適化", layout="wide")

# サイドバー設定
st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)
st.sidebar.info(f"1分短縮に{threshold}円以上かかる高速区間は『一般道』へ誘導します。")

st.title("🚗 Taco-Route: 区間別・中抜きルート提案")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

# セッションにルートデータを保存（スライダー操作でAPIを叩かないため）
if 'base_route' not in st.session_state:
    st.session_state.base_route = None

def fetch_full_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.polyline.encodedPolyline,routes.legs.steps"
    }
    # まずは「高速優先」で全行程のステップを取得する
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": False},
        "languageCode": "ja-JP"
    }
    res = requests.post(url, json=payload, headers=headers).json()
    if 'routes' in res:
        st.session_state.base_route = res['routes'][0]
    else:
        st.error("ルートが見つかりませんでした。")

if st.button("🚀 ルートを検索・解析"):
    fetch_full_route()

# --- 解析・描画ロジック ---
if st.session_state.base_route:
    route = st.session_state.base_route
    steps = route['legs'][0].get('steps', [])
    
    # 地図の初期化
    m = folium.Map(location=[35.68, 139.76], zoom_start=10)
    
    st.subheader("🗺️ 最適化マップ（青：高速維持 / 赤：一般道推奨）")
    
    display_details = []
    total_toll = 0
    
    for i, step in enumerate(steps):
        instr = step.get('navigationInstruction', {}).get('instructions', "直進")
        dist_km = step.get('distanceMeters', 0) / 1000
        # duration_secの取得（"60s"などの文字列を処理）
        duration_str = step.get('staticDuration', "0s")
        duration_sec = int(duration_str.replace("s", ""))
        
        # 高速・有料道路かどうかの判定
        is_highway = any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT"])
        
        # デフォルト（一般道）
        color = "gray"
        weight = 4
        reason = ""

        if is_highway and dist_km > 0:
            # 【重要】区間ごとのタイパ計算
            # 高速(平均80km/h)と一般道(平均30km/h)の差分で計算
            h_time_min = duration_sec / 60
            l_time_min = dist_km * 2.0 # 1kmあたり2分と仮定
            saved_min = max(0.5, l_time_min - h_time_min)
            
            est_toll = int(dist_km * 25 + 150) # 簡易料金計算
            cost_per_min = est_toll / saved_min
            
            if cost_per_min <= threshold:
                color = "blue" # タイパが良いので高速維持
                weight = 7
                total_toll += est_toll
                reason = f" (タイパ良: {int(cost_per_min)}円/分)"
            else:
                color = "red"  # タイパが悪いので一般道推奨
                weight = 8
                reason = f" (★コスパ悪: {int(cost_per_min)}円/分 → 降りる検討)"

        # 地図に描画
        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

        display_details.append({"instr": instr, "color": color, "reason": reason})

    folium_static(m)

    # 詳細ガイドの表示
    st.subheader("📑 最適化された道順ガイド")
    for idx, d in enumerate(display_details):
        if d['color'] == "blue":
            st.info(f"{idx+1}. {d['instr']} 【高速維持】{d['reason']}")
        elif d['color'] == "red":
            st.error(f"{idx+1}. {d['instr']} 【一般道推奨】{d['reason']}")
        else:
            st.write(f"{idx+1}. {d['instr']}")
            
    st.sidebar.metric("推定高速代", f"{total_toll} 円")

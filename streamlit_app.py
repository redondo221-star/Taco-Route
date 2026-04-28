import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- APIキーの設定 ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route 最終修正版", layout="wide")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

st.title("🚗 Taco-Route: 中抜き最適化")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

if 'route_steps' not in st.session_state:
    st.session_state.route_steps = None

def fetch_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        # フィールドマスクを「道路属性」まで含めて厳密に指定
        "X-Goog-Fieldmask": "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.polyline,routes.legs.steps.navigationInstruction,routes.legs.steps.travelAdvisory"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": False},
        "languageCode": "ja-JP"
    }
    
    try:
        response = requests.post(url, json=payload, headers=headers)
        res_data = response.json()
        
        if 'routes' in res_data:
            st.session_state.route_steps = res_data['routes'][0]['legs'][0].get('steps', [])
        else:
            st.error(f"ルートが見つかりません。APIエラー内容: {res_data.get('error', {}).get('message', '不明なエラー')}")
    except Exception as e:
        st.error(f"通信エラーが発生しました: {e}")

if st.button("🚀 ルートを解析"):
    fetch_route()

if st.session_state.route_steps:
    steps = st.session_state.route_steps
    m = folium.Map(location=[35.68, 139.76], zoom_start=9)
    
    st.subheader(f"📋 分析結果（1分短縮の価値が{threshold}円以上の区間を判定）")
    
    current_total_toll = 0
    
    for i, step in enumerate(steps):
        # 1. データの抽出
        dist_km = step.get('distanceMeters', 0) / 1000
        dur_sec = int(step.get('staticDuration', "0s").replace("s",""))
        instr = step.get('navigationInstruction', {}).get('instructions', "直進")
        
        # 2. 有料道路（高速）判定
        # Googleが返してくるtravelAdvisoryまたは指示文から判定
        is_toll = False
        if 'travelAdvisory' in step:
            # 道路の種類が高速道路などの場合
            is_toll = True
        elif any(kw in instr for kw in ["有料道路", "高速", "料金所", "JCT", "IC"]):
            is_toll = True
            
        color = "gray" # 一般道（デフォルト）
        weight = 4
        label = "一般道"
        
        if is_toll and dist_km > 0:
            # 3. タイパ・コスパ計算
            l_time = dist_km * 2.0  # 一般道だと1kmあたり2分と想定
            h_time = dur_sec / 60   # APIが返す高速での所要時間(分)
            saved_min = max(0.1, l_time - h_time)
            
            step_toll = int(dist_km * 25 + 150) # 推計料金
            cpm = step_toll / saved_min
            
            if cpm <= threshold:
                color = "blue" # 高速を使い続ける
                weight = 8
                label = f"🔵高速維持 ({step_toll}円/分)"
                current_total_toll += step_toll # 青い区間だけ料金を加算
                st.info(f"{i+1}. {instr} ➔ **{label}** ({int(cpm)}円/分)")
            else:
                color = "red"  # 一般道へ降りることを推奨
                weight = 8
                label = f"🔴一般道推奨 (降りて節約)"
                st.error(f"{i+1}. {instr} ➔ **{label}** (1分短縮に{int(cpm)}円もかかります)")
        else:
            # 4. 一般道区間の表示
            if dist_km > 0.3: # 短すぎる枝道は表示を省略
                st.write(f"{i+1}. {instr} (一般道走行)")

        # 5. 地図にパーツを描画
        if 'polyline' in step:
            pts = polyline.decode(step['polyline']['encodedPolyline'])
            folium.PolyLine(pts, color=color, weight=weight, opacity=0.8).add_to(m)
            if i == 0: m.location = pts[0]

    folium_static(m)
    
    # 6. サイドバーに正確な合計金額を表示
    st.sidebar.metric("この設定での推定通行料", f"{current_total_toll} 円")
    st.sidebar.caption("※青色(高速維持)と判定された区間の合計です")

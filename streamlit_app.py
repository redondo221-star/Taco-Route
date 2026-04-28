import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- 設定 ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # APIキーを入れてください

st.set_page_config(page_title="Taco-Route プロ版", layout="wide")
st.title("🚗 Taco-Route: 新4号・五霞IC最適化モデル")

st.sidebar.header("⚖️ あなたの時間価値")
threshold = st.sidebar.slider("1分短縮にいくら払える？", 0, 100, 30)
st.sidebar.write(f"設定：1分を{threshold}円以下で短縮できるなら高速推奨")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京駅")

def get_route(avoid_highways):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.legs.steps,routes.polyline,routes.duration,routes.distanceMeters"
    }
    payload = {
        "origin": {"address": origin}, "destination": {"address": destination},
        "travelMode": "DRIVE", "routingPreference": "TRAFFIC_AWARE",
        "routeModifiers": {"avoidHighways": avoid_highways}, "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 最適ルートを解析・合成する"):
    # 1. 高速ルートと一般道ルート（新4号想定）の両方を取得
    high_res = get_route(False)
    local_res = get_route(True)

    if 'routes' not in high_res or 'routes' not in local_res:
        st.error("ルートが取得できませんでした。住所を確認してください。")
    else:
        st.subheader("💡 解析結果：なぜ『新4号→五霞IC』が最強なのか")
        
        # 簡易的な比較ロジックの表示
        st.write("・新4号区間：信号が少なく平均時速が高いため、高速代を払う価値が低い（赤判定）")
        st.write("・五霞IC以南：渋滞リスクと信号が増えるため、ここから高速に乗る価値が高い（青判定）")

        m = folium.Map(location=[36.2, 139.8], zoom_start=9)
        steps = high_res['routes'][0]['legs'][0]['steps']
        
        total_toll = 0
        current_highway_dist = 0
        current_highway_saved_time = 0
        highway_buffer = []

        def process_segment(buffer, dist, saved):
            if not buffer: return 0
            toll = int(dist * 25 + 150)
            cpm = toll / max(0.1, saved)
            is_ok = cpm <= threshold
            
            color = "blue" if is_ok else "red"
            status = "【高速推奨】" if is_ok else "【下道（新4号等）推奨】"
            
            msg = f"{status} {buffer[0].get('navigationInstruction',{}).get('instructions','高速区間')}付近〜"
            if is_ok:
                st.info(f"🔵 {msg} ({int(dist)}km / {toll}円 / {int(saved)}分短縮)")
            else:
                st.error(f"🔴 {msg} (コスパ悪：1分短縮に{int(cpm)}円かかるため、下道走行を推奨)")

            for s in buffer:
                pts = polyline.decode(s['polyline']['encodedPolyline'])
                folium.PolyLine(pts, color=color, weight=8 if is_ok else 5).add_to(m)
            return toll if is_ok else 0

        # メインループ
        for step in steps:
            instr = step.get('navigationInstruction', {}).get('instructions', "")
            dist_km = step.get('distanceMeters', 0) / 1000
            dur_min = int(step.get('staticDuration', "0s").replace("s","")) / 60
            is_paid = 'travelAdvisory' in step or any(kw in instr for kw in ["有料", "高速", "首都高", "自動車道"])

            if is_paid:
                highway_buffer.append(step)
                current_highway_dist += dist_km
                # 新4号想定(時速60km=1km1分) vs 高速の実時間
                current_highway_saved_time += max(0, (dist_km * 1.0) - dur_min)
            else:
                if highway_buffer:
                    total_toll += process_segment(highway_buffer, current_highway_dist, current_highway_saved_time)
                    highway_buffer, current_highway_dist, current_highway_saved_time = [], 0, 0
                
                pts = polyline.decode(step['polyline']['encodedPolyline'])
                folium.PolyLine(pts, color="gray", weight=3).add_to(m)

        if highway_buffer:
            total_toll += process_segment(highway_buffer, current_highway_dist, current_highway_saved_time)

        folium_static(m)
        st.metric("賢く乗った場合の合計料金", f"{total_toll} 円")

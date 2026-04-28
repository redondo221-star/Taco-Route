import streamlit as st
import requests
import folium
from streamlit_folium import folium_static
import polyline

# --- 設定 ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" # 実際のキーに書き換えてください

st.set_page_config(page_title="Taco-Route 決定版", layout="wide")
st.title("🚗 Taco-Route: 新4号・五霞IC 乗り換えナビ")

st.sidebar.header("⚖️ タイパ設定")
threshold = st.sidebar.slider("1分短縮にいくら払える？", 0, 100, 30)
st.sidebar.info(f"【判定基準】1分を{threshold}円以下で短縮できるなら高速に乗ります。それ以上なら新4号等の下道を推奨します。")

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京駅")

def fetch_full_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        # 料金計算と詳細案内に必要な項目をすべて取得するよう修正
        "X-Goog-Fieldmask": "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.polyline,routes.legs.steps.navigationInstruction,routes.legs.steps.travelAdvisory,routes.polyline"
    }
    payload = {
        "origin": {"address": origin}, 
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "routeModifiers": {"avoidHighways": False}, # あえて高速込みで取得し、後で「中抜き」判定する
        "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 ルート・料金・タイパを同時解析"):
    res = fetch_full_route()
    
    if 'routes' not in res:
        st.error("ルートが取得できませんでした。住所かAPIキーを確認してください。")
    else:
        steps = res['routes'][0]['legs'][0]['steps']
        m = folium.Map(location=[36.2, 139.8], zoom_start=9)
        
        st.subheader("📍 詳細走行ガイド")
        
        total_toll = 0
        h_dist, h_saved, h_steps = 0, 0, []

        def output_highway(dist, saved, buffer):
            if not buffer: return 0
            # 首都高・高速共通の現実的な料金ロジック
            toll = int(dist * 25 + 150)
            cpm = toll / max(0.1, saved)
            is_efficient = cpm <= threshold
            
            color = "blue" if is_efficient else "red"
            icon = "🔵" if is_efficient else "🔴"
            label = "【高速を維持】" if is_efficient else "【下道（新4号）へ！】"
            
            # 代表的な場所名を取得
            place = buffer[0].get('navigationInstruction', {}).get('instructions', "高速区間")
            
            with st.expander(f"{icon} {label} {place} 付近からの区間", expanded=True):
                st.write(f"・距離: {dist:.1f}km")
                st.write(f"・料金: 約 {toll}円")
                st.write(f"・短縮時間: {int(saved)}分")
                if not is_efficient:
                    st.write(f"⚠️ 1分短縮に{int(cpm)}円かかるため、ここは「下道」が正解です！")
                
                for s in buffer:
                    st.write(f"  └ {s.get('navigationInstruction', {}).get('instructions', '')}")
                    if 'polyline' in s:
                        pts = polyline.decode(s['polyline']['encodedPolyline'])
                        folium.PolyLine(pts, color=color, weight=8, opacity=0.8).add_to(m)
            
            return toll if is_efficient else 0

        # メイン判定ループ
        for step in steps:
            instr = step.get('navigationInstruction', {}).get('instructions', "道なりに進む")
            dist_km = step.get('distanceMeters', 0) / 1000
            dur_min = int(step.get('staticDuration', "0s").replace("s","")) / 60
            
            # 有料道路判定（Googleのタグ または 特定のキーワード）
            is_paid = 'travelAdvisory' in step or any(kw in instr for kw in ["有料", "高速", "首都高", "自動車道", "IC", "JCT"])

            if is_paid:
                h_steps.append(step)
                h_dist += dist_km
                # 新4号(時速60km=1km1分) vs 高速の実時間 の差分を短縮時間とする
                h_saved += max(0, (dist_km * 1.0) - dur_min)
            else:
                # 一般道に入ったタイミングで、溜まっていた高速区間を判定
                if h_steps:
                    total_toll += output_highway(h_dist, h_saved, h_steps)
                    h_dist, h_saved, h_steps = 0, 0, []
                
                # 一般道の案内を表示（短すぎないよう詳細に出す）
                st.write(f"▶️ {instr} ({dist_km:.1f}km)")
                if 'polyline' in step:
                    pts = polyline.decode(step['polyline']['encodedPolyline'])
                    folium.PolyLine(pts, color="gray", weight=4, opacity=0.6).add_to(m)

        # 最後に残った高速区間（目的地直前など）を処理
        if h_steps:
            total_toll += output_highway(h_dist, h_saved, h_steps)

        folium_static(m)
        st.sidebar.metric("賢く乗り分けた合計料金", f"{total_toll} 円")
        st.sidebar.write("※赤色の『下道推奨』区間の料金は含んでいません。")

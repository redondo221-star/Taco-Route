import streamlit as st
import requests

# --- あなたのAPIキー ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route Pro", layout="wide")
st.title("🚗 Taco-Route: ルート詳細表示版")

threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "東京駅")
with col2:
    destination = st.text_input("目的地", "御殿場駅")

def get_full_route(avoid_highways):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        # 詳細な道順（localizedValues）とステップ（steps）を取得する設定
        "X-Goog-Fieldmask": "routes.duration,routes.distanceMeters,routes.legs.steps.navigationInstruction"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": avoid_highways},
        "languageCode": "ja-JP" # 日本語で案内を取得
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 ルートを解析して詳細を表示"):
    with st.spinner("Googleから最新ルートを取得中..."):
        res = get_full_route(avoid_highways=False) # 今回はまず高速優先の結果を表示

        if 'routes' in res:
            route = res['routes'][0]
            leg = route['legs'][0]
            
            # 1. 基本情報の表示
            st.success("✅ ルートが見つかりました")
            dist_km = route['distanceMeters'] / 1000
            duration_min = int(route['duration'][:-1]) / 60
            
            c1, c2 = st.columns(2)
            c1.metric("予想所要時間", f"{int(duration_min)} 分")
            c2.metric("走行距離", f"{dist_km:.1f} km")

            # 2. 道順（ステップ）の表示
            st.subheader("📑 詳細な道順")
            for i, step in enumerate(leg['steps']):
                # 指示文がある場合のみ表示
                if 'navigationInstruction' in step:
                    instruction = step['navigationInstruction']['instructions']
                    st.write(f"{i+1}. {instruction}")
            
            st.caption("※料金の自動計算ロジックは、この道順の中に『有料道路』という言葉が含まれているかで判定を強化できます。")

        else:
            st.error("ルートの詳細を取得できませんでした。APIキーの設定（Routes APIが有効か）を確認してください。")

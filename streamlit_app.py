import streamlit as st
import requests

# --- あなたのAPIキー ---
API_KEY = "AIzaSyAZFNWvMzl2u__9WSjF77qPhQg_1Gj6Qq8" 

st.set_page_config(page_title="Taco-Route: タイパ最適化", layout="wide")
st.title("🚗 Taco-Route: 自動ルート判定")

# 1. あなたのタイパ基準（サイドバー）
st.sidebar.header("⚖️ タイパの基準")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 10, 100, 25)
st.sidebar.caption(f"現在の設定: {threshold}円/分")
st.sidebar.info("例: 25円なら、1時間短縮に1,500円まで払うという意味です。")

# 2. 目的地入力
col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "御殿場駅")

def call_routes_api(avoid_highways):
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.duration,routes.distanceMeters,routes.legs.steps.navigationInstruction"
    }
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routeModifiers": {"avoidHighways": avoid_highways},
        "languageCode": "ja-JP"
    }
    return requests.post(url, json=payload, headers=headers).json()

if st.button("🚀 どっちがお得か判定する"):
    with st.spinner("ルートと料金を計算中..."):
        # 高速あり・なしを両方計算
        high_res = call_routes_api(False)
        low_res = call_routes_api(True)

        if 'routes' in high_res and 'routes' in low_res:
            h_route = high_res['routes'][0]
            l_route = low_res['routes'][0]

            # 時間(分)と距離(km)
            h_min = int(h_route['duration'][:-1]) / 60
            l_min = int(l_route['duration'][:-1]) / 60
            dist_km = h_route['distanceMeters'] / 1000

            # 短縮時間
            saved_min = l_min - h_min
            
            # 💡 簡易料金計算ロジック（日本の高速料金目安: 約25円/km + 入場料等）
            # 本来は詳細APIが必要ですが、まずはこれでシミュレーション！
            estimated_toll = int(dist_km * 25 + 150) if saved_min > 5 else 0
            
            # タイパコスト計算
            cost_per_min = estimated_toll / saved_min if saved_min > 0 else 0

            # 🏁 判定
            st.divider()
            if cost_per_min <= threshold and saved_min > 0:
                st.balloons()
                st.success(f"🏆 【高速道路】の利用を推奨します！")
                result_text = f"1分短縮のコストが **{cost_per_min:.1f}円** なので、あなたの基準（{threshold}円）よりお得です。"
            else:
                st.warning(f"🐢 【一般道】で行くのが賢い選択です！")
                result_text = f"高速を使っても1分短縮に **{cost_per_min:.1f}円** かかります。あなたの基準では「高い」と判断しました。"

            # 結果の表示
            st.write(result_text)
            
            c1, c2, c3 = st.columns(3)
            c1.metric("短縮される時間", f"{int(saved_min)} 分")
            c2.metric("予想高速代", f"{estimated_toll} 円")
            c3.metric("タイパ・コスト", f"{cost_per_min:.1f} 円/分")

            # 詳細な道順（高速あり）
            with st.expander("👀 具体的な道順を見る"):
                for i, step in enumerate(h_route['legs'][0]['steps']):
                    if 'navigationInstruction' in step:
                        st.write(f"{i+1}. {step['navigationInstruction']['instructions']}")
        else:
            st.error("APIの取得に失敗しました。住所を確認してください。")

import streamlit as st
import requests

# --- あなたのAPIキーを入力 ---
API_KEY = "AIzaSy..." 

st.set_page_config(page_title="Taco-Route Pro Auto", layout="wide")
st.title("🚗 Taco-Route: 自動区間提案")

# 1. ユーザー基準の設定
st.sidebar.header("⚙️ あなたの基準設定")
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)
st.sidebar.caption(f"現在の基準: {threshold}円/分")

# 2. 入力
col_in1, col_in2 = st.columns(2)
with col_in1:
    origin = st.text_input("出発地", "東京駅")
with col_in2:
    destination = st.text_input("目的地", "名古屋駅")

def get_optimized_route():
    url = "https://routes.googleapis.com/directions/v2:computeRoutes"
    headers = {
        "Content-Type": "application/json",
        "X-Goog-Api-Key": API_KEY,
        "X-Goog-Fieldmask": "routes.legs.steps.distanceMeters,routes.legs.steps.staticDuration,routes.legs.steps.navigationInstruction"
    }
    # まずは全体のルートを取得（詳細はAPIドキュメントに基づき調整）
    payload = {
        "origin": {"address": origin},
        "destination": {"address": destination},
        "travelMode": "DRIVE",
        "routingPreference": "TRAFFIC_AWARE",
        "computeAlternativeRoutes": False,
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()

if st.button("🚀 最適な乗り降りポイントを提案"):
    if not API_KEY or "AIza" not in API_KEY:
        st.error("有効なAPIキーを入力してください。")
    else:
        with st.spinner("各区間のタイパを分析中..."):
            # ここではプロトタイプとして、主要な区間（Legs）ごとの比較シミュレーションを表示します
            # 本来はRoutes APIから返る細かなStepを束ねて判定します
            
            # --- 判定シミュレーション (APIから取得した想定のデータ) ---
            segments = [
                {"section": "都心・高速入り口まで", "dist": 15, "toll": 1300, "save_min": 35},
                {"section": "郊外・バイパス区間", "dist": 80, "toll": 2500, "save_min": 15},
                {"section": "目的地周辺・渋滞区間", "dist": 20, "toll": 900, "save_min": 40},
            ]
            
            st.subheader("🏁 あなたへの最適ルート案内")
            
            total_saved_time = 0
            total_cost = 0
            
            for seg in segments:
                cost_per_min = seg["toll"] / seg["save_min"]
                
                with st.container():
                    c1, c2, c3 = st.columns([2, 1, 1])
                    c1.markdown(f"### {seg['section']}")
                    
                    if cost_per_min <= threshold:
                        c2.success("✅ 高速を利用")
                        c3.write(f"コスト: {cost_per_min:.1f}円/分")
                        total_saved_time += seg["save_min"]
                        total_cost += seg["toll"]
                    else:
                        c2.warning("🐢 一般道を推奨")
                        c3.write(f"コスト: {cost_per_min:.1f}円/分")
            
            st.divider()
            res1, res2 = st.columns(2)
            res1.metric("合計短縮時間", f"{total_saved_time} 分")
            res2.metric("合計高速料金", f"{total_cost} 円")
            
            st.info(f"💡 アドバイス: あなたの基準（{threshold}円）に基づき、タイパの悪い『{segments[1]['section']}』は下道を走るのが最も賢い選択です。")

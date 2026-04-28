import streamlit as st
import requests
import json

# --- ここにご自身のAPIキーを貼り付け ---
API_KEY = "AIzaSy..." 

st.title("🚗 Taco-Route 接続テスト版")

origin = st.text_input("出発地", "東京駅")
destination = st.text_input("目的地", "横浜駅")

if st.button("接続テスト実行"):
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
        "languageCode": "ja-JP"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    data = response.json()

    # 1. 応答の中身を全部表示（エラー特定のため）
    if response.status_code != 200:
        st.error(f"Google APIからエラーが返りました (コード: {response.status_code})")
        st.json(data) # ここに具体的な原因（Billing not enabledなど）が出ます
    elif 'routes' not in data:
        st.warning("ルートが見つかりませんでした。応答データを確認してください。")
        st.json(data)
    else:
        st.success("成功！APIは正常に動いています。")
        st.write(f"所要時間: {data['routes'][0]['duration']}")
        
        # 道順の表示テスト
        st.subheader("取得できた道順のサンプル:")
        steps = data['routes'][0]['legs'][0].get('steps', [])
        for i, step in enumerate(steps[:5]): # 最初の5ステップだけ表示
            if 'navigationInstruction' in step:
                st.write(f"{i+1}. {step['navigationInstruction']['instructions']}")

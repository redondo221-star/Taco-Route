import streamlit as st
import requests

st.set_page_config(page_title="Taco-Route Auto", layout="centered")
st.title("🤖 Taco-Route: 自動最適化ナビ")

# 1. ユーザー基準
threshold = st.sidebar.slider("1分短縮に何円まで払える？", 0, 100, 25)

# 2. 入力
st.subheader("📍 目的地を入力")
start = st.text_input("出発地", "東京駅")
end = st.text_input("目的地", "名古屋駅")

if st.button("最適な乗り継ぎを計算"):
    # --- 本来はここでGoogle Routes APIを叩き、以下のデータを取得します ---
    # 仮のシミュレーションデータ
    segments = [
        {"name": "都心区間 (東京〜海老名)", "toll": 1300, "time_saved": 40},
        {"name": "静岡区間 (御殿場〜浜松)", "toll": 3000, "time_saved": 20},
        {"name": "名古屋付近 (豊田〜名古屋)", "toll": 1200, "time_saved": 35},
    ]
    
    st.subheader("🏁 あなたへの最適提案")
    
    total_toll = 0
    total_time = 0
    instructions = []

    for seg in segments:
        cost_per_min = seg["toll"] / seg["time_saved"]
        
        if cost_per_min <= threshold:
            # 基準内なら高速利用
            status = "✅ 高速推奨"
            total_toll += seg["toll"]
            total_time += seg["time_saved"]
            instructions.append(f"{seg['name']}: **高速を利用** (1分{cost_per_min:.1f}円)")
        else:
            # 基準外なら下道利用
            status = "🐢 下道推奨"
            instructions.append(f"{seg['name']}: **一般道を利用** (1分{cost_per_min:.1f}円)")

    # 3. 結果表示
    for msg in instructions:
        st.write(msg)
        
    st.success(f"""
    **結果まとめ：**
    - 高速を使うべき区間だけ利用します。
    - 合計高速代: {total_toll}円
    - 短縮時間: {total_time}分
    """)
    
    # 最後に最適な経由地を含んだナビリンクを生成
    st.info("この指示通りにナビをセットして出発しましょう！")

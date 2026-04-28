import streamlit as st
import urllib.parse

st.set_page_config(page_title="Taco-Route Pro", layout="centered")
st.title("🚗 Taco-Route Pro")
st.caption("区間別のタイパ最適化・判断ツール")

# 1. あなたの基準（全判定に適用）
st.subheader("👤 あなたのタイパ基準")
threshold = st.slider("1分短縮に何円まで払える？", 0, 100, 25)
st.divider()

# 2. ルート分割入力
st.subheader("📍 ルートを細かく分ける")
st.write("短縮効果が場所によって違うため、区間ごとに入力してください。")

with st.expander("STEP1：場所を入力してナビを起動"):
    start = st.text_input("出発地", "東京")
    via = st.text_input("経由地（判断の分かれ目）", "御殿場")
    end = st.text_input("目的地", "名古屋")
    
    # Yahooナビ起動（経由地を考慮したリンク）
    params = {"from": start, "to": end, "via": via, "yid": "navicore"}
    y_url = f"https://map.yahoo.co.jp/route/car?{urllib.parse.urlencode(params)}"
    st.link_button("🚀 Yahoo!ナビで区間ごとの時間を確認", y_url, use_container_width=True)

st.divider()

# 3. 区間ごとのジャッジ
st.subheader("⚖️ 区間別のタイパ判定")

def segment_judge(label):
    st.markdown(f"**【{label}】**")
    c1, c2 = st.columns(2)
    with c1:
        t = st.number_input(f"高速料金", min_value=0, step=100, key=f"t_{label}")
    with c2:
        m = st.number_input(f"短縮時間(分)", min_value=1, step=1, key=f"m_{label}")
    
    cost_min = t / m if m > 0 else 0
    if t > 0:
        if cost_min <= threshold:
            st.success(f"⭕ 高速推奨 (1分{cost_min:.1f}円)")
            return t, m
        else:
            st.warning(f"🐢 下道でOK (1分{cost_min:.1f}円)")
            return 0, 0
    return 0, 0

# 各区間の判定を実行
total_cost = 0
total_saved = 0

# 区間A
cost_a, save_a = segment_judge("出発地 〜 経由地")
# 区間B
cost_b, save_b = segment_judge("経由地 〜 目的地")

# 4. 最終的な「最適ルート」の提案
st.divider()
st.subheader("🏁 本日の最適ルート提案")

res_cost = cost_a + cost_b
res_save = save_a + save_b

if res_cost > 0:
    st.info(f"""
    **おすすめの走り方：**
    判定が「⭕」の区間だけ高速を使いましょう。
    
    - 合計高速代: **{res_cost}円**
    - 合計短縮時間: **{res_save}分**
    - 全区間高速に乗るよりおトクに、かつ効率よく到着できます！
    """)
else:
    st.write("全ての区間で下道が推奨されました。のんびり行きましょう。")

import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    """
    404エラーを回避するため、利用可能なモデルを動的に取得・設定する
    """
    try:
        # 利用可能なモデルリストを取得
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1.5-flashを探す（models/gemini-1.5-flash の形式で取得される）
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        
        if not target_model:
            # flashがなければproを探す
            target_model = next((m for m in available_models if 'gemini-1.5-pro' in m), available_models[0])
            
        return genai.GenerativeModel(target_model)
    except Exception:
        # 万が一リスト取得に失敗した場合は、標準的な名称を直接指定
        return genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route Pro", layout="centered")

# --- 2. セッション状態の初期化 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route ")
st.markdown("### 最速基準・コスト削減分析モデル")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("経由地1（必須通過）", placeholder="例：佐野SA")
with col_v2:
    v2 = st.text_input("経由地2（任意）", placeholder="")

with st.expander("🔄 車両設定"):
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    input_date = st.date_input("出発日", value=st.session_state.now.date(), key="d_input")
with c2:
    input_time = st.time_input("出発時刻", value=st.session_state.now.time(), key="t_input")

# 出発日時と曜日の計算
departure_dt = datetime.combine(input_date, input_time)
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[departure_dt.weekday()]
full_dt_str = f"{departure_dt.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

# --- 4. 実行ボタン ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        # Geminiへの詳細な指示
        prompt = f"""
        あなたは日本の道路事情（バイパス、高速、ETC割引）に精通したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【絶対命令：条件】
        - 経由地 {via_points} は必ず通過すること。
        - 出発日時：{full_dt_str}（曜日・時間帯による割引と渋滞を考慮）。
        - 表記：高速道路は :red[赤文字]、一般道・バイパスは :blue[青文字]。

        【重要：比較表の作成ルール】
        最後に必ず以下の項目で比較表を作成してください。
        「案①最速タイパ」の結果を基準(0)とし、案②・案③との「差分」を計算して表示してください。

        表の構成：
        - 案名（案①最速、案②爆速コスパ、案③トータル最適）
        - 走行距離 (km)
        - 所要時間 (h:mm)
        - 高速料金 (円)
        - 基準比：距離差 (km)
        - 基準比：時間差 (分) ※案①より何分遅いか
        - 基準比：料金差 (円) ※案①より何円安いか
        - 1時間あたりの削減額 (円/h) 
          ※計算式：料金差 ÷ (時間差/60)。「時間を犠牲にして、1時間あたりいくら浮かせられたか」の指標。

        【走行条件】
        出発：{start_point} / 到着：{destination} / 車種：{vehicle}
        """

        with st.spinner(f"モデルを確認し、{full_dt_str} のルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                st.markdown(res.text)
                if v1 or v2:
                    st.info(f"💡 経由地 {via_points} を経由するルートを表示しています。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

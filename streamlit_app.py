import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import urllib.parse

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    """
    404エラー対策：利用可能なモデルを動的に検索してセットする
    """
    try:
        # 現在のAPIキーで利用可能なモデルをリストアップ
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        
        # 1.5-flashを探す（名前の中にflashが含まれるものを優先）
        target = next((m for m in available_models if '1.5-flash' in m), None)
        
        # なければ1.5-proを探す
        if not target:
            target = next((m for m in available_models if '1.5-pro' in m), available_models[0])
            
        return genai.GenerativeModel(target)
    except Exception:
        # 万が一リスト取得に失敗した場合、最も汎用的な名前を直接指定
        return genai.GenerativeModel('gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. 時刻・入力設定 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.utcnow() + timedelta(hours=9)

# タイトルからProfessionalを削除
st.title("🚗 Taco-Route")
st.markdown("### 最速基準・コスト削減分析モデル")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("経由地1（必須）", placeholder="")
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

departure_dt = datetime.combine(input_date, input_time)
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[departure_dt.weekday()]
full_dt_str = f"{departure_dt.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

# --- 4. Googleマップ用リンク生成関数 ---
def create_gmap_url(start, end, via1, via2):
    # ユニバーサルURLを使用して最も確実なルートリンクを作成
    base = "https://www.google.com/maps/dir/?api=1"
    params = {
        "origin": start,
        "destination": end,
        "travelmode": "driving"
    }
    vias = [v for v in [via1, via2] if v]
    if vias:
        params["waypoints"] = "|".join(vias)
    return base + "&" + urllib.parse.urlencode(params)

# --- 5. 実行ボタン ---
if st.button("🚀 プロの推奨ルートを提案してもらう"):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        prompt = f"""
        あなたは日本の道路事情（バイパス、高速、ETC割引）に精通したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【絶対条件】
        - 経由地 {via_points} は必ず通過すること。
        - 高速道路は :red[赤文字]、一般道・バイパスは :blue[青文字] で記載。
        - 案ごとに、文字記号を使った「簡易ルート図」を必ず作成して視覚化すること。
          例：[出発地] === :red[高速名] === (経由地) --- :blue[バイパス名] --- [目的地]

        【重要：比較表の作成ルール】
        案①（最速）の結果を基準(0)とし、案②・案③との「差分」を計算して表示してください。
        項目：走行距離(km)、所要時間(h:mm)、高速料金(円)、距離差(km)、時間差(分)、料金差(円)、1時間あたりの削減額(円/h)
        ※削減額計算：料金差 ÷ (時間差/60)

        【走行条件】
        出発：{start_point} / 到着：{destination} / 車種：{vehicle} / 出発日時：{full_dt_str}
        """

        with st.spinner(f"最適なモデルを選択し、ルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                
                st.markdown("---")
                st.markdown(f"## 🏁 {full_dt_str} 出発の提案結果")
                
                # 地図リンクボタン
                gmap_link = create_gmap_url(start_point, destination, v1, v2)
                st.link_button("📍 このルートをGoogleマップで開く（詳細・ナビ）", gmap_link)
                
                st.markdown(res.text)
                
            except Exception as e:
                if "429" in str(e):
                    st.error("⚠️ AIの利用制限（1日分）に達しました。明日またお試しいただくか、新しいAPIキーを設定してください。")
                else:
                    st.error(f"エラーが発生しました: {e}")

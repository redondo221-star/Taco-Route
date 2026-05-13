import streamlit as st
import google.generativeai as genai
from datetime import datetime
import urllib.parse
import re
from streamlit_mic_recorder import speech_to_text

# --- 1. アプリ基本設定 (必ず最初に書く) ---
st.set_page_config(page_title="Taco-Route", layout="centered", page_icon="🚗")

# --- 2. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    try:
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target_model = next((m for m in available_models if 'gemini-1.5-flash' in m), None)
        if not target_model:
            target_model = next((m for m in available_models if 'gemini-1.5-pro' in m), available_models[0])
        return genai.GenerativeModel(target_model)
    except Exception:
        return genai.GenerativeModel('gemini-1.5-flash')

# --- 3. セッション状態の初期化 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.now()
if "route_chat" not in st.session_state:
    st.session_state.route_chat = []

# --- 4. メインUI構成 ---
st.title("🚗 Taco-Route")
st.markdown("### 最速基準・コスト削減分析モデル")

st.subheader("📍 ルート検索設定")
start_point = st.text_input("出発地点", value="宇都宮駅", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", value="大阪駅", placeholder="例：大阪駅")

col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地", placeholder="例：佐野SA")
with col_v2:
    v2 = st.text_input("任意経由地", placeholder="")

col_vh, col_dt = st.columns([1, 1])
with col_vh:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

with col_dt:
    st.write("🕒 出発日時")
    input_date = st.date_input("日付", value=st.session_state.now.date(), key="d_input")
    input_time = st.time_input("時刻", value=st.session_state.now.time(), key="t_input")

departure_dt = datetime.combine(input_date, input_time)
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[departure_dt.weekday()]
full_dt_str = f"{departure_dt.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

st.markdown("---")

# --- 5. 実行ボタン（最初の提案） ---
if st.button("🚀 この条件でルートを提案してもらう", use_container_width=True):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        st.session_state.route_chat = [] # 履歴リセット
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        prompt = f"""
        プロドライバーとして3つのルートを提案して。
        経由地：{via_points}、出発日時：{full_dt_str}、車種：{vehicle}
        回答の末尾に必ず DATA_START ... DATA_END 形式で地図用データを含めること。
        出発：{start_point} / 到着：{destination}
        """

        with st.spinner("解析中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.session_state.route_chat.append({"role": "assistant", "content": res.text})
            except Exception as e:
                st.error(f"エラー: {e}")

# --- 6. チャット履歴と地図の表示 ---
for message in st.session_state.route_chat:
    clean_content = message["content"].split("DATA_START")[0]
    with st.chat_message(message["role"]):
        st.markdown(clean_content)

if st.session_state.route_chat:
    last_res = st.session_state.route_chat[-1]["content"]
    if "DATA_START" in last_res:
        st.markdown("### 📍 地図を確認")
        data_part = last_res.split("DATA_START")[1].split("DATA_END")[0]
        btn_labels = ["①最速", "②爆速コスパ", "③トータル最適"]
        for i, label in enumerate(btn_labels):
            match = re.search(f"ROUTE{i+1}:(.*)", data_part)
            if match:
                pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                encoded_path = "/".join([urllib.parse.quote(p) for p in pts])
                gmap_url = f"https://www.google.com/maps/dir/{encoded_path}"
                st.link_button(f"🗺️ {label}の地図を表示", gmap_url, use_container_width=True)

    # --- 7. 対話機能（音声入力 ＆ キーボード） ---
    st.markdown("---")
    st.subheader("💬 AIと対話・追加指示")
    
    # 音声入力
    audio_text = speech_to_text(start_prompt="🎤 声で指示を出す", language='ja', key='speech')
    # キーボード入力
    query = st.chat_input("さらに質問...")

    # 音声があれば上書き
    if audio_text:
        query = audio_text

    if query:
        st.session_state.route_chat.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        with st.spinner("AIが回答中..."):
            model = get_working_model()
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.route_chat[-3:]])
            response = model.generate_content(f"履歴を踏まえて回答して:\n{history_text}\n質問: {query}")
            st.session_state.route_chat.append({"role": "assistant", "content": response.text})
            st.rerun()

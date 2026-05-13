import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
import urllib.parse
import re
from streamlit_mic_recorder import speech_to_text # 音声入力用

# --- 1. アプリ基本設定 (必ず最初に実行) ---
st.set_page_config(page_title="Taco-Route", layout="centered")

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
    st.session_state.route_chat = [] # 対話履歴用

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
    input_date = st.date_input("日付", value=st.session_state.now.date(), key="d_input", label_visibility="collapsed")
    input_time = st.time_input("時刻", value=st.session_state.now.time(), key="t_input", label_visibility="collapsed")

departure_dt = datetime.combine(input_date, input_time)
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[departure_dt.weekday()]
full_dt_str = f"{departure_dt.strftime('%Y年%m月%d日')}({day_of_week}) {input_time.strftime('%H:%M')}"

st.markdown("---")

# --- 5. 実行ボタン（初回提案） ---
if st.button("🚀 この条件でルートを提案してもらう", use_container_width=True):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        st.session_state.route_chat = [] # 新規検索時は履歴リセット
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        prompt = f"""
        あなたは日本の道路事情（バイパス、高速、ETC割引）に精通したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【絶対命令：条件】
        - 経由地 {via_points} は必ず通過すること。
        - 出発日時：{full_dt_str}（割引と渋滞を考慮）。
        - 表記ルール：高速道路・有料道路名は :red[== 道路名 (〇〇IC〜××IC) ==] のように赤文字で。
        - 表記ルール：一般道・バイパス名は :blue[-- 道路名 --] のように青文字で。
        - 各案の解説には必ず「所要時間」と「高速料金」を含めること。

        【重要：比較表の作成】
        各案の詳細解説のあと、必ず Markdown形式で比較表を作成してください。
        項目：案名 | 距離(km) | 所要時間 | 高速料金(円) | 距離差 | 時間差(分) | 料金差(円) | 1時間あたりの削減額

        【地図表示用データ】
        回答の最末尾に、Googleマップ生成用の地点リストを以下の形式で出力してください。
        DATA_START
        ROUTE1:{start_point},[入口IC],[出口IC],{destination}
        ROUTE2:{start_point},[主要バイパス],[入口IC],[出口IC],{destination}
        ROUTE3:{start_point},[主要地点],{destination}
        DATA_END

        出発：{start_point} / 到着：{destination} / 車種：{vehicle}
        """

        with st.spinner(f"最適ルートを解析中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                if res.text:
                    st.session_state.route_chat.append({"role": "assistant", "content": res.text})
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# --- 6. 履歴表示と追加機能 ---
for message in st.session_state.route_chat:
    display_content = message["content"].split("DATA_START")[0]
    with st.chat_message(message["role"]):
        st.markdown(display_content)

# 最新の提案に基づく地図ボタンの表示
if st.session_state.route_chat:
    last_content = st.session_state.route_chat[-1]["content"]
    if "DATA_START" in last_content:
        st.markdown("---")
        st.subheader("📍 Googleマップでルートを確認")
        data_part = last_content.split("DATA_START")[1].split("DATA_END")[0]
        btn_labels = ["①最速ルート", "②爆速コスパ", "③トータル最適"]
        
        for i, label in enumerate(btn_labels):
            match = re.search(f"ROUTE{i+1}:(.*)", data_part)
            if match:
                pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                final_pts = [start_point] + pts[1:-1] + [destination]
                encoded_path = "/".join([urllib.parse.quote(p) for p in final_pts])
                gmap_url = f"https://www.google.com/maps/dir/{encoded_path}"
                st.link_button(f"🗺️ {label}の地図を表示", gmap_url, use_container_width=True)

    # --- 7. 対話・音声入力セクション ---
    st.markdown("---")
    st.subheader("💬 AIと対話・追加指示")
    
    # 音声入力ボタン
    audio_text = speech_to_text(start_prompt="🎤 声で指示を出す", stop_prompt="停止", language='ja', key='speech')
    # チャット入力
    query = st.chat_input("例：案②をもう少し詳しく / 途中で寄れるおすすめのSAは？")

    # 音声入力があればqueryを上書き
    if audio_text:
        query = audio_text

    if query:
        st.session_state.route_chat.append({"role": "user", "content": query})
        with st.chat_message("user"):
            st.markdown(query)
        
        with st.spinner("AIが回答を生成中..."):
            model = get_working_model()
            # 文脈を維持するため直近のやり取りを送信
            history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.route_chat[-3:]])
            response = model.generate_content(f"これまでの提案を踏まえて回答して:\n{history_context}\n質問: {query}")
            st.session_state.route_chat.append({"role": "assistant", "content": response.text})
            st.rerun()

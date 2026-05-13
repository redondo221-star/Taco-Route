import streamlit as st
import google.generativeai as genai
from datetime import datetime
import urllib.parse
import re

# --- 1. API・モデル設定 ---
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

# スマホで見やすくするため、標準レイアウトに設定
st.set_page_config(page_title="Taco-Route", layout="centered", page_icon="🚗")

# --- 2. セッション状態の初期化 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.now()
if "route_chat" not in st.session_state:
    st.session_state.route_chat = []  # チャット履歴用

# --- 3. メインUI構成 ---
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

# --- 4. 実行ボタン ---
if st.button("🚀 この条件でルートを提案してもらう", use_container_width=True):
    if not start_point or not destination:
        st.warning("出発地点と目的地を入力してください。")
    else:
        st.session_state.route_chat = [] # 履歴をリセット
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        prompt = f"""
        あなたは日本の道路事情に精通したプロドライバーです。
        以下の条件で3つのルート（案①最速、案②爆速コスパ、案③トータル最適）を提案してください。

        【条件】
        - 経由地 {via_points} は必ず通過すること。
        - 出発日時：{full_dt_str}。
        - 表記：高速道路名は :red[== 道路名 (〇〇IC〜××IC) ==]、一般道は :blue[-- 道路名 --]。
        - 各案に「所要時間」「高速料金」を含めること。
        - 最後に Markdown形式で比較表を作成すること。

        【地図用データ】
        回答の末尾に必ず以下を含めてください。
        DATA_START
        ROUTE1:{start_point},[中継点],{destination}
        ROUTE2:{start_point},[中継点],{destination}
        ROUTE3:{start_point},[中継点],{destination}
        DATA_END

        出発：{start_point} / 到着：{destination} / 車種：{vehicle}
        """

        with st.spinner("最適ルートを解析中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.session_state.route_chat.append({"role": "assistant", "content": res.text})
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

# --- 5. チャット・履歴表示 ---
for message in st.session_state.route_chat:
    # 地図データ部分は非表示にしてメッセージを表示
    clean_content = message["content"].split("DATA_START")[0]
    with st.chat_message(message["role"]):
        st.markdown(clean_content)

# 最新の回答から地図ボタンを生成
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

    # 追加質問の入力欄
    if query := st.chat_input("例：案②をもっと詳しく / 途中で寄れる温泉を教えて"):
        with st.chat_message("user"):
            st.markdown(query)
        st.session_state.route_chat.append({"role": "user", "content": query})
        
        with st.spinner("AIが回答を考えています..."):
            model = get_working_model()
            # 過去のやり取りを含めて質問
            history_text = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.route_chat[-3:]])
            response = model.generate_content(f"これまでのルート提案を踏まえて答えてください:\n{history_text}\nユーザー: {query}")
            st.session_state.route_chat.append({"role": "assistant", "content": response.text})
            st.rerun()

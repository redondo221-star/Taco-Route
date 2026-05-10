import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta
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
st.set_page_config(page_title="Taco-Route", layout="centered")

# --- 2. セッション状態の初期化 ---
if "now" not in st.session_state:
    st.session_state.now = datetime.now()

# --- 3. メインUI構成 ---
st.title("🚗 Taco-Route")
st.markdown("### 最速基準・コスト削減分析モデル")

# 全ての入力をメイン画面に配置
st.subheader("📍 ルート検索設定")

# 地点入力
start_point = st.text_input("出発地点", value="宇都宮駅", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", value="大阪駅", placeholder="例：大阪駅")

# 経由地（スマホで見やすいよう、少しコンパクトに）
col_v1, col_v2 = st.columns(2)
with col_v1:
    v1 = st.text_input("必須経由地", placeholder="例：佐野SA")
with col_v2:
    v2 = st.text_input("任意経由地", placeholder="")

# 車種と日時の設定
col_vh, col_dt = st.columns([1, 1])
with col_vh:
    vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)

with col_dt:
    st.write("🕒 出発日時")
    input_date = st.date_input("日付", value=st.session_state.now.date(), key="d_input", label_visibility="collapsed")
    input_time = st.time_input("時刻", value=st.session_state.now.time(), key="t_input", label_visibility="collapsed")

# 出発日時と曜日の計算
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
        via_points = f"「{v1}」" if v1 else ""
        if v2: via_points += f" および 「{v2}」"

        # Geminiへの指示：以前の表形式を維持しつつ、MAP用地点データを最後に出力させる
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
        「行ってこい」を防ぐため、地点は [出発地, 入口IC名, 出口IC名, 目的地] のように最小限かつ順番通りに。
        
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
                    full_text = res.text
                    display_content = full_text.split("DATA_START")[0]
                    
                    st.success(f"解析完了: {full_dt_str} 出発")
                    
                    # メインの解説と表を表示
                    st.markdown(display_content)
                    
                    # --- MAPボタンの生成処理 ---
                    if "DATA_START" in full_text:
                        st.markdown("---")
                        st.subheader("📍 Googleマップでルートを確認")
                        data_part = full_text.split("DATA_START")[1].split("DATA_END")[0]
                        
                        # スマホだと横並びボタンは小さすぎるため、縦に並べるかcontainerを使う
                        btn_labels = ["①最速ルート", "②爆速コスパ", "③トータル最適"]
                        
                        for i, label in enumerate(btn_labels):
                            match = re.search(f"ROUTE{i+1}:(.*)", data_part)
                            if match:
                                pts = [p.strip() for p in match.group(1).split(",") if p.strip()]
                                # 入口・出口を明確にしたURL生成
                                final_pts = [start_point] + pts[1:-1] + [destination]
                                encoded_path = "/".join([urllib.parse.quote(p) for p in final_pts])
                                gmap_url = f"https://www.google.com/maps/dir/{encoded_path}"
                                
                                st.link_button(f"🗺️ {label}の地図を表示", gmap_url, use_container_width=True)

                    if v1 or v2:
                        st.info(f"💡 経由地 {via_points} を考慮した結果です。")
            except Exception as e:
                st.error(f"エラーが発生しました: {e}")

import streamlit as st
import google.generativeai as genai
from datetime import datetime, timedelta

# --- 1. API・モデル設定 ---
if "API_KEY" in st.secrets:
    genai.configure(api_key=st.secrets["API_KEY"])

def get_working_model():
    try:
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        target = next((m for m in models if 'gemini-1.5-flash' in m), models[0])
        return genai.GenerativeModel(target)
    except:
        return genai.GenerativeModel('models/gemini-1.5-flash')

st.set_page_config(page_title="Taco-Route Pro", layout="centered")

# --- 2. 日本時間計算（初期値用） ---
now_jst = datetime.utcnow() + timedelta(hours=9)

st.title("🚗 Taco-Route Professional")
st.markdown("### 熟練ドライバー仕様・最適化モデル")

# --- 3. 入力フォーム ---
start_point = st.text_input("出発地点", placeholder="例：宇都宮駅")
destination = st.text_input("目的地", value="ルートイン和泉岸和田")

with st.expander("🔄 車両・コスト詳細設定"):
    v1 = st.text_input("経由地1")
    v2 = st.text_input("経由地2")
    col1, col2 = st.columns(2)
    with col1:
        vehicle = st.radio("車種", ["普通車", "軽自動車"], horizontal=True)
    with col2:
        # 【修正】100円刻みに変更
        time_val = st.number_input("時間価値 (円/h)", value=1500, step=100)

st.write("🕒 出発日時設定")
c1, c2 = st.columns(2)
with c1:
    dep_date = st.date_input("出発日", value=now_jst.date())
with c2:
    # 【修正】時刻が確実に変数 dep_time に格納されるように構成
    dep_time = st.time_input("出発時刻", value=now_jst.time())

# --- 4. 曜日計算とプロンプト生成 ---
# AIの曜日勘違いを防ぐため、Python側で曜日を確定させる
weeks = ["月", "火", "水", "木", "金", "土", "日"]
day_of_week = weeks[dep_date.weekday()]
full_date_str = f"{dep_date.strftime('%Y年%m月%d日')}({day_of_week})"
time_str = dep_time.strftime('%H:%M')

if st.button("🚀 プロの最適ルートを提案してもらう"):
    if not start_point:
        st.warning("出発地点を入力してください。")
    else:
        # 【修正】ユーザーが選択した日付と時刻をプロンプトに厳格に反映
        prompt = f"""
        あなたは日本中の道を走り尽くしたベテランドライバーです。
        以下の「指定された日時」の交通状況を考慮して、最適なルートを提案してください。

        【厳守する出発日時】
        {full_date_str} {time_str} 出発
        （※AIの内部カレンダーではなく、この日付と曜日を正としてください）

        【走行条件】
        出発地：{start_point} / 目的地：{destination} / 経由地：{v1}, {v2}
        車種：{vehicle} / 時間価値：{time_val}円/h

        【ベテランの鉄則】
        1. 信号回避：新4号、名阪国道など「無料爆速区間」を高速の代替として優先活用すること。
        2. 都市部ショートカット：東北道から大泉・関西方面へ抜ける際、圏央道より「外環道経由」が速くて安い場合は迷わず選択すること。
        3. 実戦的最適化：案③「トータル最適」は、渋滞リスクが低く、定速走行が可能で、時間価値を含めた総コストが最小となる「プロが選ぶ勝利ルート」にすること。

        【出力】
        - 案①：【最速タイパ】有料道路フル活用
        - 案②：【爆速コスパ】無料高規格道活用で高速代激減
        - 案③：【トータル最適】時間価値を考慮した「プロの推奨」

        ※計算式は出さず、比較表と「なぜこのルートが賢いのか」の解説を重視してください。
        """

        with st.spinner(f"{full_date_str} {time_str} の最適ルートを計算中..."):
            try:
                model = get_working_model()
                res = model.generate_content(prompt)
                st.markdown("---")
                st.markdown(f"### 🕒 {full_date_str} {time_str} 出発の提案")
                st.markdown(res.text)
                st.info("💡 曜日や時間帯によるETC割引（深夜・休日）を考慮した提案です。")
            except Exception as e:
                st.error(f"AIエラー: {e}")

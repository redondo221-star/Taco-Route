import streamlit as st

st.set_page_config(page_title="AIルート相談プロンプト生成器", layout="centered")

st.title("🤖 AIにルートを相談するための条件設定")
st.write("ここで条件を入れると、GeminiやCopilotに最適なルートを尋ねるための依頼文が作成されます。")

# 入力項目
col1, col2 = st.columns(2)
with col1:
    origin = st.text_input("出発地", "栃木県宇都宮駅")
with col2:
    destination = st.text_input("目的地", "東京都中央区（東京駅付近）")

st.divider()

# こだわり条件
st.subheader("⚙️ こだわり条件")
threshold = st.select_slider(
    "1分短縮にいくらまで払える？（タイパ設定）",
    options=[10, 20, 30, 50, 100, 200],
    value=30
)

option_route4 = st.checkbox("新4号バイパス（宇都宮〜五霞）の活用を検討に含める", value=True)
option_etc = st.checkbox("ETC深夜割引（0-4時）を考慮する", value=False)

if st.button("✨ AIへの質問文を生成する"):
    # プロンプトの組み立て
    prompt = f"""
あなたは日本の道路事情に精通したベテランドライバーです。
以下の条件で、最も「コスパとタイパのバランスが良い」車ルートを教えてください。

# 移動区間
出発地：{origin}
目的地：{destination}

# 判断基準
・私は「1分短縮できるなら{threshold}円まで」なら高速代を払います。
・それ以上のコストがかかる場合は、積極的に下道（バイパス等）を使いたいと考えています。
"""
    
    if option_route4:
        prompt += "\n# 特別な指示\n・宇都宮〜五霞間は『新4号バイパス』が非常に流れが良く、高速と遜色ないスピードで走れる場合があります。この区間の東北道利用が本当に見合うか厳しく判定してください。\n"
    
    if option_etc:
        prompt += "・ETC深夜割引（30%OFF）が適用される前提で計算してください。\n"

    prompt += """
# 回答してほしい内容
1. 最終的な推奨ルート（どのICで乗り、どのICで降りるか）
2. 想定される高速料金の合計
3. そのルートを選んだ理由（下道と比べて何分早くなり、いくら高くなるか）
4. 通過する主要な国道やバイパス名

親切で具体的なアドバイスをお願いします。
"""

    st.subheader("📋 下の文章をコピーしてAI（Gemini/Copilot）に貼り付けてください")
    st.code(prompt, language="markdown")
    st.success("このプロンプトをAIに渡せば、複雑な料金や地元の道路事情を加味した納得の回答が得られます！")

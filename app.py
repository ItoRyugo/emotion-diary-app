print("✅ app.py が起動されました")

from flask import Flask, render_template, request
import openai
from dotenv import load_dotenv
import os
import json
import csv
from datetime import datetime

# .env 読み込み
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# SDKバージョン0.x系のため models.list() は使用不可
# ↓以下は必要ならコメントアウトして残してもOK
# try:
#     models = openai.models.list()
#     print("✅ APIキーは有効です。利用可能なモデル数:", len(models.data))
# except openai.error.AuthenticationError:
#     print("❌ APIキーが無効です。")
# except Exception as e:
#     print("⚠️ APIキーの確認中にエラー:", str(e))

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    text = request.form["diary"]
    mode = request.form.get("mode", "gentle")  # デフォルトは優しいモード

    if mode == "strict":
        comment_prompt = (
            f"その次の行に、**感情分析に基づいた厳しい一言アドバイス**を『コメント: ○○○』の形式で必ず書いてください。\n"
            f"コメントは冷静で論理的だが、優しさは不要。厳しさとカリスマ性を持って、相手に喝を入れてください。\n"
            f"以下のようなスタイルを参考に：\n"
            f"- 『逃げていても現実は変わらない。立ち向かえ。』\n"
            f"- 『言い訳はやめろ。やるか、やらないかだ。』\n"
            f"- 『感情に流されるな。お前が変わらなきゃ誰が変える。』\n"
            f"語尾は断言口調にすること（〜だ、〜しろ、〜あるのみ、など）。\n"
        )
    else:
        comment_prompt = (
            f"その次の行に、**感情分析に基づいた『親身で思いやりのあるコメント』を『コメント: ○○○』の形式で必ず書いてください。**\n"
            f"コメントは、相手の気持ちを受け止め、安心感と温かみを与えながら、前向きな一歩をそっと応援するようなものにしてください。\n"
            f"以下のようなスタイルを参考に：\n"
            f"- 『今はしんどくても、あなたのペースで進めば大丈夫。無理しすぎないでね。』\n"
            f"- 『気持ちを言葉にできたこと自体がすごい。少しずつでいい、歩いていこう。』\n"
            f"- 『一人で抱えなくていいよ。あなたの感情は、ちゃんと意味がある。』\n"
        )

    prompt = (
        f"以下の文章から感情を分類し、喜び・怒り・哀しみ・楽しさ・不安・その他の6つの割合（%）をJSON形式で出力してください。\n"
        f"出力形式：{{'喜び':40,'怒り':10,'哀しみ':20,'楽しさ':15,'不安':10,'その他':5}}\n\n"
        + comment_prompt +
        f"\n文章:\n{text}"
    )

    # ✅ 正しいAPI呼び出し形式（v0系向け）
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{
            "role": "user",
            "content": prompt
        }]
    )

    result = response.choices[0].message["content"]
    print("GPTからの返答:", result)

    if "コメント:" in result:
        json_part, feedback = result.split("コメント:", 1)
    else:
        json_part = result
        feedback = "（コメントが見つかりませんでした）"

    try:
        emotions = json.loads(json_part.strip())
    except json.JSONDecodeError:
        emotions = {"喜び": 0, "怒り": 0, "哀しみ": 0, "楽しさ": 0, "不安": 0, "その他": 0}
        feedback = "⚠️ 感情データの解析に失敗しました。"

    # CSVに保存
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_file = "logs/emotion_log.csv"
    os.makedirs("logs", exist_ok=True)
    with open(log_file, "a", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([now, text, emotions, feedback.strip()])

    return render_template(
        "result.html",
        emotions=emotions,
        feedback=feedback.strip(),
        mode=mode
    )

@app.route("/history")
def history():
    log_file = "logs/emotion_log.csv"
    logs = []
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            reader = csv.reader(f)
            for row in reader:
                if len(row) == 4:
                    try:
                        emotions_dict = json.loads(row[2].replace("'", '"'))
                        logs.append({
                            "datetime": row[0],
                            "text": row[1],
                            "emotions": emotions_dict,
                            "feedback": row[3]
                        })
                    except json.JSONDecodeError:
                        continue
    return render_template("history.html", logs=logs)

@app.route("/test")
def test():
    print("✅ /test にアクセスされました")
    return "Test OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)


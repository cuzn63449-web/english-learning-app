from flask import Flask, render_template, jsonify, request
from database import get_db
from datetime import date, timedelta

app = Flask(__name__)

# === 页面路由 ===
@app.route("/")
def index():
    return render_template("index.html", page="home")

@app.route("/study")
def study():
    return render_template("study.html", page="study")

@app.route("/vocabulary")
def vocabulary():
    return render_template("vocabulary.html", page="vocab")

@app.route("/exercises")
def exercises():
    return render_template("exercises.html", page="exercises")

@app.route("/stats")
def stats():
    return render_template("stats.html", page="stats")

@app.route("/reading")
def reading():
    return render_template("reading.html", page="reading")

@app.route("/wordbook")
def wordbook():
    return render_template("wordbook.html", page="wordbook")

@app.route("/oral")
def oral():
    return render_template("oral.html", page="exercises")


# === SM-2 算法 ===
def sm2_calc(progress, result):
    ef = progress["ease_factor"]
    interval = progress["interval_days"]
    reps = progress["repetitions"] + 1
    streak = progress["correct_streak"]

    if result == "correct":
        streak += 1
        if interval == 0:
            interval = 1
        elif interval == 1:
            interval = 3
        else:
            interval = round(interval * ef)
        ef = max(1.3, ef + 0.1)
        status = "mastered" if streak >= 3 else "learning"
    elif result == "fuzzy":
        streak = 0
        interval = max(1, round(interval * 0.5))
        ef = max(1.3, ef - 0.2)
        status = "learning"
    else:  # wrong
        streak = 0
        interval = 1
        ef = max(1.3, ef - 0.3)
        status = "learning"

    next_review = (date.today() + timedelta(days=interval)).isoformat()
    return {
        "ease_factor": round(ef, 1),
        "interval_days": interval,
        "repetitions": reps,
        "correct_streak": streak,
        "status": status,
        "next_review_date": next_review,
        "last_review_date": date.today().isoformat(),
        "last_review_result": result
    }


# === 学习 API ===
@app.route("/api/study/start")
def api_study_start():
    level = request.args.get("level", "考研")
    db = get_db()
    today = date.today().isoformat()

    due = db.execute("""
        SELECT up.id as pid, up.is_marked, up.next_review_date, up.status as prog_status,
               w.* FROM user_word_progress up
        JOIN words w ON up.word_id = w.id
        WHERE up.next_review_date <= ? AND up.status != 'mastered' AND w.level = ?
        ORDER BY up.next_review_date ASC LIMIT 12
    """, (today, level)).fetchall()

    words = []
    seen_ids = set()

    for r in due:
        if len(words) >= 10:
            break
        seen_ids.add(r["word_id"])
        d = dict(r)
        d["is_marked"] = bool(r["is_marked"])
        d["is_review"] = True
        words.append(d)

    # 不够10个，补新词
    if len(words) < 10:
        new = db.execute("""
            SELECT w.* FROM words w
            WHERE w.id NOT IN (SELECT word_id FROM user_word_progress) AND w.level = ?
            ORDER BY RANDOM()
            LIMIT ?
        """, (level, 10 - len(words))).fetchall()

        for r in new:
            if len(words) >= 10:
                break
            d = dict(r)
            d["is_marked"] = False
            d["is_review"] = False
            words.append(d)

    db.close()
    return jsonify(words)


@app.route("/api/study/result", methods=["POST"])
def api_study_result():
    data = request.get_json()
    word_id = data["word_id"]
    result = data["result"]  # correct / fuzzy / wrong

    db = get_db()
    today = date.today().isoformat()

    # 获取或创建进度记录
    prog = db.execute(
        "SELECT * FROM user_word_progress WHERE word_id = ?", (word_id,)
    ).fetchone()

    if not prog:
        db.execute(
            "INSERT INTO user_word_progress (word_id, status, next_review_date) VALUES (?, 'new', ?)",
            (word_id, today)
        )
        db.commit()
        prog = db.execute(
            "SELECT * FROM user_word_progress WHERE word_id = ?", (word_id,)
        ).fetchone()

    # SM-2计算
    updated = sm2_calc(dict(prog), result)

    db.execute("""
        UPDATE user_word_progress SET
            status=?, ease_factor=?, interval_days=?, repetitions=?,
            correct_streak=?, next_review_date=?, last_review_date=?, last_review_result=?
        WHERE word_id=?
    """, (
        updated["status"], updated["ease_factor"], updated["interval_days"],
        updated["repetitions"], updated["correct_streak"],
        updated["next_review_date"], updated["last_review_date"],
        updated["last_review_result"], word_id
    ))

    # 更新每日记录
    existing = db.execute(
        "SELECT id FROM study_log WHERE study_date=?", (today,)
    ).fetchone()
    if existing:
        db.execute(
            "UPDATE study_log SET words_learned=words_learned+1 WHERE study_date=?",
            (today,)
        )
    else:
        db.execute(
            "INSERT INTO study_log (study_date, words_learned) VALUES (?, 1)",
            (today,)
        )

    db.commit()

    # 返回今日进度
    due = db.execute(
        "SELECT COUNT(*) as n FROM user_word_progress WHERE next_review_date <= ?",
        (today,)
    ).fetchone()["n"]
    mastered = db.execute(
        "SELECT COUNT(*) as n FROM user_word_progress WHERE status='mastered'"
    ).fetchone()["n"]
    db.close()

    return jsonify({
        "updated": updated,
        "review_due": due,
        "mastered": mastered
    })


@app.route("/api/study/toggle_mark", methods=["POST"])
def api_toggle_mark():
    data = request.get_json()
    word_id = data["word_id"]
    db = get_db()
    prog = db.execute("SELECT * FROM user_word_progress WHERE word_id=?", (word_id,)).fetchone()
    if not prog:
        db.execute("INSERT INTO user_word_progress (word_id, is_marked) VALUES (?, 1)", (word_id,))
        db.commit()
        marked = True
    else:
        new_val = 0 if prog["is_marked"] else 1
        db.execute("UPDATE user_word_progress SET is_marked=? WHERE word_id=?", (new_val, word_id))
        db.commit()
        marked = new_val == 1
    db.close()
    return jsonify(marked=marked)

@app.route("/api/words/marked")
def api_marked_words():
    db = get_db()
    rows = db.execute("""
        SELECT w.*, up.is_marked FROM words w
        JOIN user_word_progress up ON w.id = up.word_id
        WHERE up.is_marked = 1 ORDER BY w.word
    """).fetchall()
    db.close()
    return jsonify([dict(r) for r in rows])


# === 聊天 API ===
@app.route("/api/chat", methods=["POST"])
def api_chat():
    data = request.get_json()
    user_msg = data.get("message", "")
    history = data.get("history", [])

    db = get_db()
    learned = db.execute("""
        SELECT w.word, w.meaning FROM words w
        JOIN user_word_progress up ON w.id = up.word_id
        WHERE up.status IN ('learning','mastered') ORDER BY RANDOM() LIMIT 30
    """).fetchall()
    total = db.execute("SELECT COUNT(*) as n FROM words").fetchone()["n"] or 0
    mastered = db.execute(
        "SELECT COUNT(*) as n FROM user_word_progress WHERE status='mastered'"
    ).fetchone()["n"] or 0
    db.close()

    word_ctx = ""
    if learned:
        word_ctx = "\n用户已掌握/正在学的词汇：\n" + "\n".join([f"- {r['word']} ({r['meaning']})" for r in learned])

    system = f"""你是考研英语AI助教，也是用户的私人英语教练。用户词汇量{mastered}/{total}。{word_ctx}

**核心能力：**
1. 用已学词汇出选择题/完形填空（必须模仿真题格式，每道题标注考点）
2. 生成阅读理解短文+题目（文章和题目全部英文，考研真题风格）
3. 出写作题并批改作文
4. 分析英文文章
5. 解答英语学习问题

**出题铁律：**
- 所有题目、选项、文章、问题**必须全部用英文**！
- 每道题必须有明确**考点**（语法点/固定搭配/词义辨析/逻辑关系/熟词生义等）
- 出题风格模仿考研英语一/二真题
- 出题时**不显示答案**，只给题目和选项
- 只有用户明确说"对答案""看答案""答案是什么"才公布

**批改规则（关键！）：**
- 你出的题目就在上方对话历史里，用户可以只说"1A 2C 3B"
- 你**必须自己从对话历史中找到你出的题**，然后逐题对答案
- 不要反问用户"你答的是哪道题"
- 逐题批改："第1题 ✅ / 第1题 ❌ 正确答案是X（解析：考点是...）"
- 批改完统计正确率+给鼓励

**写作批改：**
- 从语法、用词、句式、逻辑四个维度评价
- 指出错误位置+修改建议+润色版

**语气：简洁+鼓励+网感。用**加粗**突出重点。"""

    # 拼接历史上下文到消息中
    history_text = ""
    if history:
        recent = history[-6:]  # 最近3轮对话
        history_text = "\n\n--- 对话历史 ---\n"
        for h in recent:
            role = "👤 用户" if h["role"] == "user" else "🤖 AI"
            history_text += f"{role}: {h['content']}\n"
        history_text += "--- 以上是对话历史，下面是用户最新消息 ---\n\n"

    full_msg = history_text + user_msg

    from ai_client import chat
    reply = chat(full_msg, system, 1500)
    return jsonify({"reply": reply})


# === AI练习 API（保留旧端点兼容）===
@app.route("/api/exercises/quiz", methods=["POST"])
def api_exercises_quiz():
    db = get_db()
    learned = db.execute("""
        SELECT w.word, w.meaning FROM words w
        JOIN user_word_progress up ON w.id = up.word_id
        WHERE up.status IN ('learning','mastered') ORDER BY RANDOM() LIMIT 30
    """).fetchall()
    db.close()
    if len(learned) < 5:
        return jsonify({"error": "先学一些单词再来吧！至少需要5个已学词汇"}), 400

    word_list = "\n".join([f"{r['word']} — {r['meaning']}" for r in learned])
    prompt = f"""用以下用户已学的词汇，出5道完形填空选择题。每道题在句中留一个空，给4个选项（标记正确答案）。
格式：每道题{{
  "sentence": "含__blank__的英文句子",
  "blank_word": "正确答案",
  "options": ["选项A","选项B","选项C","选项D"]
}}
返回纯JSON数组。
用户已学单词：
{word_list}"""

    from ai_client import chat
    resp = chat(prompt, "你是考研英语出题专家。只返回JSON数组，不要其他内容。", 1500)
    try:
        questions = json.loads(resp.strip().strip("`").strip("json").strip())
        return jsonify({"questions": questions})
    except:
        return jsonify({"raw": resp, "questions": []})


@app.route("/api/exercises/reading", methods=["POST"])
def api_exercises_reading():
    db = get_db()
    learned = db.execute("""
        SELECT w.word, w.meaning FROM words w
        JOIN user_word_progress up ON w.id = up.word_id
        WHERE up.status IN ('learning','mastered') ORDER BY RANDOM() LIMIT 25
    """).fetchall()
    db.close()
    if len(learned) < 10:
        return jsonify({"error": "至少需要10个已学词汇才能生成阅读"}), 400

    word_list = ", ".join([r["word"] for r in learned])
    prompt = f"""用以下词汇写一篇150-200词的英文短文，然后出3道阅读理解选择题（4选1，标正确答案）。
返回JSON：{{"title": "...", "passage": "...", "questions": [{{"question": "...", "options": ["A","B","C","D"], "answer": 0}}]}}
词汇：{word_list}"""

    from ai_client import chat
    resp = chat(prompt, "你是考研英语阅读出题专家。只返回JSON。", 1500)
    try:
        data = json.loads(resp.strip().strip("`").strip("json").strip())
        return jsonify(data)
    except:
        return jsonify({"raw": resp, "passage": resp, "title": "", "questions": []})


@app.route("/api/exercises/writing", methods=["POST"])
def api_exercises_writing():
    data = request.get_json() or {}
    mode = data.get("mode", "prompt")  # prompt or correct
    user_text = data.get("text", "")

    db = get_db()
    learned = db.execute("""
        SELECT w.word FROM words w
        JOIN user_word_progress up ON w.id = up.word_id
        WHERE up.status IN ('learning','mastered') ORDER BY RANDOM() LIMIT 20
    """).fetchall()
    db.close()
    word_list = ", ".join([r["word"] for r in learned]) if learned else "常用考研词汇"

    from ai_client import chat

    if mode == "prompt":
        prompt = f"出一道考研英语写作题（议论文或应用文），要求尽量用到以下词汇：{word_list}。返回JSON：{{\"title\": \"...\", \"requirement\": \"...\", \"word_count\": 150, \"hint_words\": [\"word1\",\"word2\"]}}"
        resp = chat(prompt, "你是考研英语写作出题专家。只返回JSON。", 500)
        try:
            return jsonify(json.loads(resp.strip().strip("`").strip("json").strip()))
        except:
            return jsonify({"title": "写作练习", "requirement": resp, "hint_words": []})

    else:  # correct
        prompt = f"""请批改以下英语作文。从语法、用词、句式、逻辑四个维度评价，给出修改建议，然后提供润色版。
建议使用的词汇：{word_list}

学生作文：
{user_text}

返回JSON：{{"score": 85, "grammar": ["错误1","错误2"], "vocabulary": ["建议1"], "structure": ["建议1"], "overall": "总体评价", "revised": "润色后全文"}}"""
        resp = chat(prompt, "你是考研英语写作批改专家。只返回JSON。", 1200)
        try:
            return jsonify(json.loads(resp.strip().strip("`").strip("json").strip()))
        except:
            return jsonify({"overall": resp, "score": 0, "grammar": [], "vocabulary": [], "structure": [], "revised": ""})


# === 词汇 API ===
@app.route("/api/words")
def api_words():
    q = request.args.get("q", "").strip()
    level = request.args.get("level", "").strip()
    page = int(request.args.get("page", 1))
    per = 30
    offset = (page - 1) * per

    db = get_db()
    where = "WHERE 1=1"
    params = []
    if q:
        where += " AND (word LIKE ? OR meaning LIKE ?)"
        params.extend([f"%{q}%", f"%{q}%"])
    if level:
        where += " AND level = ?"
        params.append(level)

    count = db.execute(f"SELECT COUNT(*) as n FROM words {where}", params).fetchone()["n"]
    rows = db.execute(
        f"SELECT * FROM words {where} ORDER BY word LIMIT ? OFFSET ?",
        params + [per, offset]
    ).fetchall()
    db.close()
    return jsonify({
        "words": [dict(r) for r in rows],
        "total": count, "page": page, "pages": max(1, (count + per - 1) // per)
    })

@app.route("/api/words/<int:word_id>")
def api_word_detail(word_id):
    db = get_db()
    w = db.execute("SELECT * FROM words WHERE id=?", (word_id,)).fetchone()
    if not w:
        db.close()
        return jsonify({"error": "not found"}), 404
    meanings = db.execute("SELECT * FROM word_meanings WHERE word_id=?", (word_id,)).fetchall()
    points = db.execute("SELECT * FROM word_exam_points WHERE word_id=?", (word_id,)).fetchall()
    prog = db.execute("SELECT * FROM user_word_progress WHERE word_id=?", (word_id,)).fetchone()
    db.close()
    return jsonify({
        "word": dict(w),
        "meanings": [dict(m) for m in meanings],
        "exam_points": [dict(p) for p in points],
        "progress": dict(prog) if prog else None
    })

# === 通用 API ===
@app.route("/api/stats")
def api_stats():
    db = get_db()
    total = db.execute("SELECT COUNT(*) as n FROM words").fetchone()["n"] or 0
    mastered = db.execute(
        "SELECT COUNT(*) as n FROM user_word_progress WHERE status='mastered'"
    ).fetchone()["n"] or 0
    learning = db.execute(
        "SELECT COUNT(*) as n FROM user_word_progress WHERE status='learning'"
    ).fetchone()["n"] or 0
    review_due = db.execute(
        "SELECT COUNT(*) as n FROM user_word_progress WHERE next_review_date <= date('now','localtime') AND status!='mastered'"
    ).fetchone()["n"] or 0
    today = db.execute(
        "SELECT words_learned, words_reviewed FROM study_log WHERE study_date=date('now','localtime')"
    ).fetchone()
    today_words = today["words_learned"] if today else 0
    today_reviewed = today["words_reviewed"] if today else 0

    # 计算连续天数
    dates = db.execute(
        "SELECT study_date FROM study_log ORDER BY study_date DESC LIMIT 365"
    ).fetchall()
    streak = 0
    from datetime import date as dt, timedelta
    check = dt.today()
    for d in dates:
        d_str = d["study_date"]
        if d_str == check.isoformat():
            streak += 1
            check -= timedelta(days=1)
        elif d_str == (check - timedelta(days=1)).isoformat():
            continue
        else:
            break

    # 近7天学习量
    week = []
    for i in range(6, -1, -1):
        day = (dt.today() - timedelta(days=i)).isoformat()
        row = db.execute(
            "SELECT words_learned FROM study_log WHERE study_date=?", (day,)
        ).fetchone()
        week.append({"date": day[5:], "count": row["words_learned"] if row else 0})

    db.close()
    return jsonify(streak=streak, today_words=today_words, today_reviewed=today_reviewed,
                   review_due=review_due, total_words=total, mastered=mastered,
                   learning=learning, week=week)


@app.route("/api/cost")
def api_cost():
    db = get_db()
    total = db.execute("SELECT COALESCE(SUM(amount),0) as n FROM cost_log").fetchone()["n"]
    month = db.execute(
        "SELECT COALESCE(SUM(amount),0) as n FROM cost_log WHERE strftime('%Y-%m',created_at)=strftime('%Y-%m','now')"
    ).fetchone()["n"]
    calls = db.execute("SELECT COUNT(*) as n FROM cost_log").fetchone()["n"]
    db.close()
    return jsonify(total=total, month=month, calls=calls, budget=10.0)


# 启动时初始化数据库
from database import init_db
init_db()

if __name__ == "__main__":
    app.run(debug=True)

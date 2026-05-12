import csv
import os
import re
from database import get_db, init_db

CSV_FILE = os.path.join(os.path.dirname(__file__), "2025kaoyan5500.csv")

POS_MAP = {
    "n.": "n.", "v.": "v.", "vt.": "vt.", "vi.": "vi.",
    "adj.": "adj.", "adv.": "adv.", "prep.": "prep.",
    "pron.": "pron.", "conj.": "conj.", "art.": "art.",
    "num.": "num.", "int.": "int.", "abbr.": "abbr.",
    "aux.": "aux.", "det.": "det.", "interj.": "interj."
}


def extract_pos(meaning):
    for pos in POS_MAP:
        if meaning.startswith(pos):
            return pos, meaning[len(pos):].strip()
    return "", meaning


def import_csv():
    init_db()
    db = get_db()

    with open(CSV_FILE, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        rows = list(reader)

    imported = 0
    skipped = 0

    for i, row in enumerate(rows):
        if not row or not row[0].strip():
            continue
        word = row[0].strip()
        meaning_raw = row[1].strip() if len(row) > 1 else ""

        # 跳过空释义（专有名词等CSV解析失败的词）
        if not meaning_raw or len(meaning_raw) < 2:
            print(f"  skip empty: {word}")
            skipped += 1
            continue

        # 多行释义合并
        meaning_raw = meaning_raw.replace("\n", "; ")

        # 提取词性
        pos, meaning = extract_pos(meaning_raw)

        # 简单音标（CSV不含，后续AI补全）
        phonetic = ""

        try:
            db.execute(
                "INSERT OR IGNORE INTO words (word, phonetic, part_of_speech, meaning, level) VALUES (?, ?, ?, ?, ?)",
                (word, phonetic, pos, meaning, "考研")
            )
            if db.total_changes > 0:
                imported += 1
            else:
                skipped += 1
        except Exception as e:
            print(f"  skip {word}: {e}")
            skipped += 1

    db.commit()
    total = db.execute("SELECT COUNT(*) as n FROM words").fetchone()["n"]
    db.close()

    print(f"导入完成: 新增 {imported} 词, 跳过 {skipped} (重复), 总计 {total} 词")


if __name__ == "__main__":
    import_csv()

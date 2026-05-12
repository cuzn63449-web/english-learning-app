import json, hashlib, time
from database import get_db

import os
DEEPSEEK_KEY = os.environ.get("DEEPSEEK_KEY", "sk-60f08f34907143ffa93ed451eb2d3b65")
DEEPSEEK_URL = "https://api.deepseek.com/v1/chat/completions"

# 费用估算（DeepSeek V3）
COST_PER_1K_INPUT = 0.00014   # ¥/1K tokens
COST_PER_1K_OUTPUT = 0.00028  # ¥/1K tokens


def _hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def _record_cost(amount, tokens, operation):
    db = get_db()
    db.execute("INSERT INTO cost_log (amount, tokens_used, operation) VALUES (?,?,?)",
               (amount, tokens, operation))
    db.commit()
    db.close()


def chat(prompt, system="", max_tokens=800):
    """调用DeepSeek，带缓存+费用记录"""
    import urllib.request

    cache_key = _hash(system + prompt)
    db = get_db()
    cached = db.execute(
        "SELECT response FROM ai_cache WHERE cache_key=? AND model='deepseek'",
        (cache_key,)
    ).fetchone()
    if cached:
        db.close()
        return cached["response"]

    body = {
        "model": "deepseek-chat",
        "messages": [],
        "max_tokens": max_tokens,
        "temperature": 0.7
    }
    if system:
        body["messages"].append({"role": "system", "content": system})
    body["messages"].append({"role": "user", "content": prompt})

    data = json.dumps(body).encode()
    req = urllib.request.Request(DEEPSEEK_URL, data=data, headers={
        "Authorization": f"Bearer {DEEPSEEK_KEY}",
        "Content-Type": "application/json"
    })

    start = time.time()
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read().decode())

    content = result["choices"][0]["message"]["content"]
    in_tokens = result.get("usage", {}).get("prompt_tokens", 0)
    out_tokens = result.get("usage", {}).get("completion_tokens", 0)
    cost = (in_tokens / 1000) * COST_PER_1K_INPUT + (out_tokens / 1000) * COST_PER_1K_OUTPUT

    db.execute(
        "INSERT OR IGNORE INTO ai_cache (cache_key, prompt_hash, response, model, tokens_used) VALUES (?,?,?,?,?)",
        (cache_key, _hash(prompt), content, "deepseek", in_tokens + out_tokens)
    )
    db.commit()
    db.close()

    _record_cost(round(cost, 6), in_tokens + out_tokens, "chat")
    return content

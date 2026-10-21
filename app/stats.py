# -*- coding: utf-8 -*-
"""泰院 AI 学长 - 运营日报：统计提问日志与反馈日志，输出数据看板"""
import json
import os
import sys
from collections import Counter

sys.stdout.reconfigure(encoding="utf-8")  # Windows 控制台编码兜底

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")


def read_jsonl(name):
    path = os.path.join(LOG_DIR, name)
    if not os.path.exists(path):
        return []
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    rows.append(json.loads(line))
                except json.JSONDecodeError:
                    pass  # 坏行跳过，不影响统计
    return rows


def main():
    chats = read_jsonl("chat_log.jsonl")
    feedbacks = read_jsonl("feedback_log.jsonl")

    total = len(chats)
    if total == 0:
        print("还没有数据：先去 http://localhost:8000 聊几句吧")
        return

    hits = [c for c in chats if c.get("hit_id")]
    hit_rate = len(hits) / total * 100

    ups = [f for f in feedbacks if f.get("rating") == "up"]
    downs = [f for f in feedbacks if f.get("rating") == "down"]
    fb_total = len(ups) + len(downs)
    sat_rate = len(ups) / fb_total * 100 if fb_total else 0

    print("=" * 44)
    print("📊 泰院 AI 学长 · 运营日报")
    print("=" * 44)
    print(f"提问总数：{total}")
    print(f"知识库命中率：{hit_rate:.0f}%（{len(hits)}/{total}）")
    print(f"未解决率：{100 - hit_rate:.0f}%")
    print(f"回答满意率：{sat_rate:.0f}%（{len(ups)} 赞 / {len(downs)} 踩，共 {fb_total} 条反馈）")
    print()

    # 差评清单：问题 + 命中条目 + 回答摘要，按流程分类处理
    print("-" * 44)
    print("👎 差评清单（答错改答案 / 答不全补充 / 答非所问改检索词 / 语气改prompt）")
    print("-" * 44)
    if downs:
        for f in reversed(downs):  # 最新的差评排最前
            q = f.get("question", "")
            hit_id, reply = None, ""
            for c in reversed(chats):
                if c.get("question") == q:
                    hit_id = c.get("hit_id")
                    reply = c.get("reply", "")[:40]
                    break
            where = f"命中条目 #{hit_id}" if hit_id else "未命中"
            print(f"· {q}  ({f.get('time', '')})")
            print(f"  {where} ｜ 回答：{reply}…")
    else:
        print("暂无")

    # 未命中排行：高频的补进 FAQ
    misses = Counter(c.get("question", "") for c in chats if not c.get("hit_id"))
    print("-" * 44)
    print("❓ 未命中问题排行（高频的补进 FAQ）")
    print("-" * 44)
    if misses:
        for q, n in misses.most_common(10):
            print(f"· {q} × {n}")
    else:
        print("暂无")

    # 热门条目排行：新生最关心什么
    hit_counter = Counter(c.get("hit_id") for c in chats if c.get("hit_id"))
    print("-" * 44)
    print("📈 热门问题排行（新生最关心什么）")
    print("-" * 44)
    if hit_counter:
        faq = {}
        faq_path = os.path.join(PROJECT_ROOT, "docs", "faq.json")
        if os.path.exists(faq_path):
            with open(faq_path, encoding="utf-8") as fh:
                for item in json.load(fh):
                    faq[item["id"]] = item["question"]
        for hit_id, n in hit_counter.most_common(10):
            print(f"· #{hit_id} {faq.get(hit_id, '?')} × {n}")
    else:
        print("暂无")


if __name__ == "__main__":
    main()

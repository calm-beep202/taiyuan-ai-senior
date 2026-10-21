# -*- coding: utf-8 -*-
"""泰院 AI 学长 - 骨架版：调用混元 API 的基础对话循环"""
import json
import os
import urllib.request

# ---------- 从项目根目录 .env 读取配置 ----------
def load_env():
    env = {}
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(project_root, ".env"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                env[k.strip()] = v.strip()
    return env


env = load_env()
API_KEY = env["HUNYUAN_API_KEY"]
BASE_URL = env["HUNYUAN_BASE_URL"]
MODEL = env["HUNYUAN_MODEL"]

SYSTEM_PROMPT = (
    "你是「泰院 AI 学长」，泰山学院的校园问答助手。"
    "说话像热心的学长：自然、口语化、简洁，多用短句。"
    "不要提\"校园知识\"\"知识库\"\"根据资料\"这类词。"
    "诚实但不扫兴：答不了的细节简单说明还没整理到并给个建议，别整段拒绝。"
)


# ---------- 核心函数：发送消息列表，返回模型回复 ----------
def chat(messages):
    data = json.dumps(
        {"model": MODEL, "messages": messages, "stream": False}
    ).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + "/chat/completions",
        data=data,
        headers={
            "Authorization": "Bearer " + API_KEY,
            "Content-Type": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    return body["choices"][0]["message"]["content"]


# 疑问泛词：本身信息量低，命中只给低权重，避免抢走正确条目
GENERIC_WORDS = {"什么时候", "几号", "几点", "怎么", "如何", "多少", "多久", "哪里", "哪儿", "什么"}


# ---------- 校园知识库：加载 FAQ + 关键词检索 ----------
def load_faq():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    with open(os.path.join(project_root, "docs", "faq.json"), encoding="utf-8") as f:
        return json.load(f)


def retrieve(question, faq):
    """关键词匹配，返回得分最高的 FAQ 条目；没有实词命中返回 None"""
    best, best_score = None, 0
    for item in faq:
        score = 0
        for kw in item["keywords"]:
            if kw in question:
                score += 3 if kw in GENERIC_WORDS else 10  # 疑问泛词信息量低，降权
        if score > best_score:
            best, best_score = item, score
    return best if best_score >= 10 else None


def build_context(question, faq, hit=None):
    """检索知识库，组装给模型的指令：
    - 命中：知识覆盖的部分自然回答，没覆盖的点只说明没整理到，不整段拒绝
    - 未命中：诚实兜底，引导转人工，禁止编造
    hit 参数允许调用方传入已算好的检索结果，避免重复检索
    """
    if hit is None:
        hit = retrieve(question, faq)
    if hit:
        return (
            f"【校园知识】\n问：{hit['question']}\n答：{hit['answer']}\n\n"
            "【规则】上面的内容供你参考：覆盖到的部分直接自然回答，别整段复述原文；"
            "用户问的点上面没有时，只对那一点说\"这块我还没整理到\"并给个建议，其余照常回答。\n\n"
            f"用户问题：{question}"
        )
    return (
        "【规则】先看对话历史：用户问的内容如果之前的对话里已经聊过，直接结合历史回答。"
        "历史里也没有的，以学长口吻自然说明暂时答不上来，建议到新生群问学长学姐。"
        "别编造，别提\"知识库\"这类词。\n\n"
        f"用户问题：{question}"
    )


# ---------- 对话循环 ----------
def main():
    print("=== 泰院 AI 学长（MVP 版）===")
    print("输入 quit 退出\n")
    faq = load_faq()
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    while True:
        try:
            user_input = input("你：")
        except EOFError:
            break
        if user_input.strip().lower() == "quit":
            break
        messages.append({"role": "user", "content": build_context(user_input, faq)})
        try:
            reply = chat(messages)
        except Exception as e:
            reply = f"[调用出错] {e}"
        messages.append({"role": "assistant", "content": reply})
        print("学长：" + reply)


if __name__ == "__main__":
    main()

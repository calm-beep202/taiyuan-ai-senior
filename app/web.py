# -*- coding: utf-8 -*-
"""泰院 AI 学长 - 网页版：本地 HTTP 服务，浏览器直接聊（无需安装任何东西）"""
import datetime
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from chat import chat, build_context, load_faq, retrieve

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(PROJECT_ROOT, "app", "static")
LOG_DIR = os.path.join(PROJECT_ROOT, "logs")
PORT = 8000
FAQ = load_faq()  # 启动时加载一次


def log_jsonl(name, obj):
    """追加一条日志（JSON Lines 格式，一行一条，方便事后统计）"""
    os.makedirs(LOG_DIR, exist_ok=True)
    with open(os.path.join(LOG_DIR, name), "a", encoding="utf-8") as f:
        f.write(json.dumps(obj, ensure_ascii=False) + "\n")


class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            with open(os.path.join(STATIC_DIR, "index.html"), encoding="utf-8") as f:
                body = f.read().encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        if self.path == "/api/chat":
            self.handle_chat()
        elif self.path == "/api/feedback":
            self.handle_feedback()
        else:
            self._send_json({"error": "not found"}, 404)

    def handle_chat(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            raw = self.rfile.read(length).decode("utf-8")
            messages = json.loads(raw)["messages"]  # 完整历史，最后一条是用户刚发的
        except (UnicodeDecodeError, json.JSONDecodeError, KeyError):
            self._send_json({"error": "bad request"}, 400)
            return
        question = messages[-1]["content"]
        # 检索 + 注入知识库（历史原样保留，多轮上下文）
        hit = retrieve(question, FAQ)
        messages[-1] = {"role": "user", "content": build_context(question, FAQ, hit)}
        try:
            reply = chat(messages)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)
            return
        # 埋点：提问日志（命中条目 id、问题、回答）
        log_jsonl("chat_log.jsonl", {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "question": question,
            "hit_id": hit["id"] if hit else None,
            "reply": reply[:200],
        })
        self._send_json({"reply": reply})

    def handle_feedback(self):
        length = int(self.headers.get("Content-Length", 0))
        try:
            raw = self.rfile.read(length).decode("utf-8")
            data = json.loads(raw)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._send_json({"error": "bad request"}, 400)
            return
        # 埋点：满意度（up=有帮助 / down=没帮助）
        log_jsonl("feedback_log.jsonl", {
            "time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "rating": data.get("rating"),
            "question": data.get("question", ""),
        })
        self._send_json({"ok": True})

    def log_message(self, fmt, *args):
        pass  # 不打印每条请求，保持终端干净


def main():
    print(f"泰院 AI 学长已启动：http://localhost:{PORT}")
    print("手机访问：和电脑连同一个 WiFi，浏览器打开 http://<电脑IP>:{PORT}")
    print("（查电脑IP：终端输入 ipconfig，看 IPv4 地址；首次运行如弹防火墙提示请点允许）")
    print("按 Ctrl+C 停止服务")
    ThreadingHTTPServer(("0.0.0.0", PORT), Handler).serve_forever()


if __name__ == "__main__":
    main()

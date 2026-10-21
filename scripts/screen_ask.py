"""Background hotkey tool: Ctrl+Alt+Q -> drag a screen region -> Claude reads the text and answers.

    pythonw screen_ask.py [--key Q] [--model MODEL] [--prompt TEXT]

Backend: Anthropic API when ANTHROPIC_API_KEY is set, otherwise the `claude -p` CLI
(uses the existing Claude Code login).
"""
import argparse
import base64
import ctypes
import ctypes.wintypes as wt
import os
import queue
import shutil
import subprocess
import sys
import threading
import tkinter as tk
from tkinter import messagebox

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from snip import default_out, set_dpi_aware, snip  # noqa: E402

user32 = ctypes.windll.user32
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
WM_HOTKEY = 0x0312
API_MODEL = "claude-sonnet-5-5"
FONT = ("Microsoft JhengHei", 11)

DEFAULT_PROMPT = (
    "這張圖是使用者從螢幕上框選的區域。請：\n"
    "1. 【辨識文字】照原樣列出圖中文字（表格、選項保持結構，看不清楚標 [?]）。\n"
    "2. 【回答】圖中每個問題逐題作答：選擇題給選項與一兩句理由；計算題列算式；"
    "錯誤訊息給原因與修法。若沒有問題，給重點摘要或翻譯。\n"
    "用繁體中文回答，簡潔。"
)


def hotkey_thread(vk, events):
    if not user32.RegisterHotKey(None, 1, MOD_CONTROL | MOD_ALT | MOD_NOREPEAT, vk):
        events.put(("error", "熱鍵已被占用（可能已經在執行中）。"))
        return
    events.put(("ready", None))
    msg = wt.MSG()
    while user32.GetMessageW(ctypes.byref(msg), None, 0, 0) != 0:
        if msg.message == WM_HOTKEY:
            events.put(("snip", None))


def ask_api(path, prompt, model):
    import anthropic

    with open(path, "rb") as f:
        data = base64.standard_b64encode(f.read()).decode()
    resp = anthropic.Anthropic().messages.create(
        model=model or API_MODEL,
        max_tokens=4096,
        messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
            {"type": "text", "text": prompt},
        ]}],
    )
    return "".join(b.text for b in resp.content if b.type == "text")


def ask_cli(path, prompt, model):
    exe = shutil.which("claude")
    if not exe:
        raise RuntimeError("找不到 claude 指令，也沒有設定 ANTHROPIC_API_KEY。")
    cmd = [exe, "-p", f"用 Read 工具讀取圖片 {path}\n\n{prompt}",
           "--allowedTools", "Read", "--output-format", "text"]
    if model:
        cmd += ["--model", model]
    r = subprocess.run(cmd, cwd=os.path.dirname(path), capture_output=True,
                       stdin=subprocess.DEVNULL, timeout=300,
                       creationflags=subprocess.CREATE_NO_WINDOW)
    out = r.stdout.decode("utf-8", "replace").strip()
    if r.returncode != 0 or not out:
        raise RuntimeError(r.stderr.decode("utf-8", "replace").strip() or f"claude exit {r.returncode}")
    return out


class App:
    def __init__(self, args):
        self.args = args
        self.events = queue.Queue()
        self.busy = False
        self.root = tk.Tk()
        self.root.withdraw()
        self.ask = ask_api if os.environ.get("ANTHROPIC_API_KEY") else ask_cli
        vk = ord(args.key.upper())
        threading.Thread(target=hotkey_thread, args=(vk, self.events), daemon=True).start()
        self.root.after(100, self.poll)

    def poll(self):
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "error":
                    messagebox.showerror("螢幕問答", payload)
                    self.root.destroy()
                    return
                if kind == "ready":
                    self.toast(f"螢幕問答已啟動：Ctrl+Alt+{self.args.key.upper()} 框選")
                elif kind == "snip" and not self.busy:
                    self.do_snip()
                elif kind == "answer":
                    win, text = payload
                    self.show(win, text)
        except queue.Empty:
            pass
        self.root.after(100, self.poll)

    def toast(self, text, ms=2500):
        t = tk.Toplevel(self.root)
        t.overrideredirect(True)
        t.attributes("-topmost", True)
        tk.Label(t, text=text, font=FONT, bg="#222", fg="white", padx=14, pady=8).pack()
        t.update_idletasks()
        t.geometry(f"+{self.root.winfo_screenwidth() - t.winfo_width() - 30}+40")
        t.after(ms, t.destroy)

    def do_snip(self):
        self.busy = True
        # Hide open answer windows so they don't end up in the screenshot.
        shown = [w for w in self.root.winfo_children() if isinstance(w, tk.Toplevel) and w.winfo_viewable()]
        for w in shown:
            w.withdraw()
        self.root.update()
        try:
            img = snip(self.root)
        finally:
            self.busy = False
            for w in shown:
                if w.winfo_exists():
                    w.deiconify()
        if img is None:
            return
        path = default_out()
        img.save(path)
        win = self.answer_window()
        threading.Thread(target=self.work, args=(path, win), daemon=True).start()

    def work(self, path, win):
        try:
            text = self.ask(path, self.args.prompt, self.args.model)
        except Exception as e:  # shown to the user in the answer window
            text = f"⚠ 失敗：{e}"
        self.events.put(("answer", (win, text)))

    def answer_window(self):
        win = tk.Toplevel(self.root)
        win.title("螢幕問答")
        win.attributes("-topmost", True)
        sw = self.root.winfo_screenwidth()
        win.geometry(f"560x480+{sw - 600}+80")
        bar = tk.Frame(win)
        bar.pack(side="bottom", fill="x")
        txt = tk.Text(win, wrap="word", font=FONT, padx=10, pady=8)
        sb = tk.Scrollbar(win, command=txt.yview)
        txt.configure(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True)
        txt.insert("1.0", "Claude 思考中…")
        txt.configure(state="disabled")
        win.txt = txt

        def copy():
            self.root.clipboard_clear()
            self.root.clipboard_append(txt.get("1.0", "end").strip())

        for label, cmd in (("複製", copy), ("再框一次", lambda: self.events.put(("snip", None))),
                           ("關閉", win.destroy), ("結束程式", self.root.destroy)):
            tk.Button(bar, text=label, font=FONT, command=cmd).pack(side="left", padx=4, pady=4)
        win.bind("<Escape>", lambda e: win.destroy())
        return win

    def show(self, win, text):
        if not win.winfo_exists():
            return
        win.txt.configure(state="normal")
        win.txt.delete("1.0", "end")
        win.txt.insert("1.0", text)
        win.txt.configure(state="disabled")
        win.lift()

    def run(self):
        self.root.mainloop()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--key", default="Q", help="hotkey letter used with Ctrl+Alt (default Q)")
    ap.add_argument("--model", help=f"model (API default {API_MODEL}; CLI default = claude's own)")
    ap.add_argument("--prompt", default=DEFAULT_PROMPT, help="instruction sent with the image")
    args = ap.parse_args()
    set_dpi_aware()
    App(args).run()


if __name__ == "__main__":
    main()

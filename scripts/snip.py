"""Freeze the screen, let the user drag a rectangle, save the region as PNG.

CLI:  python snip.py [--delay SEC] [--out PATH]
      prints the saved PNG path; exit code 1 if cancelled (Esc / right click).
Lib:  snip(master) -> PIL.Image or None  (used by screen_ask.py)
"""
import argparse
import ctypes
import os
import sys
import tempfile
import time
import tkinter as tk
from datetime import datetime

from PIL import Image, ImageEnhance, ImageGrab, ImageTk

user32 = ctypes.windll.user32


def set_dpi_aware():
    # Physical pixels everywhere, so Tk coords match ImageGrab coords on scaled displays.
    try:
        user32.SetProcessDpiAwarenessContext(ctypes.c_void_p(-4))  # PER_MONITOR_AWARE_V2
    except Exception:
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            user32.SetProcessDPIAware()


def virtual_screen():
    return (user32.GetSystemMetrics(76), user32.GetSystemMetrics(77),
            user32.GetSystemMetrics(78), user32.GetSystemMetrics(79))


def snip(master):
    """Show a fullscreen overlay over all monitors; return the cropped image or None."""
    vx, vy, vw, vh = virtual_screen()
    shot = ImageGrab.grab(all_screens=True)
    if shot.size != (vw, vh):
        shot = shot.resize((vw, vh))
    dim = ImageEnhance.Brightness(shot).enhance(0.55)

    win = tk.Toplevel(master)
    win.overrideredirect(True)
    win.attributes("-topmost", True)
    win.geometry(f"{vw}x{vh}+{vx}+{vy}")
    canvas = tk.Canvas(win, width=vw, height=vh, highlightthickness=0, cursor="crosshair")
    canvas.pack()
    bg = ImageTk.PhotoImage(dim)
    canvas.create_image(0, 0, image=bg, anchor="nw")
    # Hint centered on the primary monitor, whose top-left is screen (0, 0).
    canvas.create_text(user32.GetSystemMetrics(0) // 2 - vx, 30 - vy,
                       text="拖曳框選要辨識的區域　(Esc / 右鍵取消)",
                       fill="white", font=("Microsoft JhengHei", 16, "bold"))

    state = {"start": None, "rect": None, "lit": None, "lit_img": None, "box": None}

    def on_press(e):
        state["start"] = (e.x, e.y)
        state["rect"] = canvas.create_rectangle(e.x, e.y, e.x, e.y, outline="#ff3b30", width=2)

    def on_drag(e):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        canvas.coords(state["rect"], x0, y0, e.x, e.y)
        l, t, r, b = min(x0, e.x), min(y0, e.y), max(x0, e.x), max(y0, e.y)
        # Show the selected area at full brightness.
        if r - l > 1 and b - t > 1:
            state["lit_img"] = ImageTk.PhotoImage(shot.crop((l, t, r, b)))
            if state["lit"]:
                canvas.coords(state["lit"], l, t)
                canvas.itemconfigure(state["lit"], image=state["lit_img"])
            else:
                state["lit"] = canvas.create_image(l, t, image=state["lit_img"], anchor="nw")
            canvas.tag_raise(state["rect"])

    def on_release(e):
        if not state["start"]:
            return
        x0, y0 = state["start"]
        l, t, r, b = min(x0, e.x), min(y0, e.y), max(x0, e.x), max(y0, e.y)
        if r - l >= 5 and b - t >= 5:
            state["box"] = (l, t, r, b)
        win.destroy()

    def cancel(_e=None):
        win.destroy()

    canvas.bind("<ButtonPress-1>", on_press)
    canvas.bind("<B1-Motion>", on_drag)
    canvas.bind("<ButtonRelease-1>", on_release)
    canvas.bind("<Button-3>", cancel)
    win.bind("<Escape>", cancel)
    win.focus_force()
    win.grab_set()
    master.wait_window(win)
    return shot.crop(state["box"]) if state["box"] else None


def default_out():
    d = os.path.join(tempfile.gettempdir(), "screen-ask")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, datetime.now().strftime("snip_%Y%m%d_%H%M%S.png"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--delay", type=float, default=0, help="seconds to wait before freezing the screen")
    ap.add_argument("--out", help="output PNG path (default: %%TEMP%%\\screen-ask\\snip_*.png)")
    args = ap.parse_args()

    set_dpi_aware()
    if args.delay > 0:
        time.sleep(args.delay)
    root = tk.Tk()
    root.withdraw()
    img = snip(root)
    root.destroy()
    if img is None:
        print("cancelled", file=sys.stderr)
        sys.exit(1)
    out = args.out or default_out()
    img.save(out)
    print(out)


if __name__ == "__main__":
    main()

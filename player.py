"""回放器：用 SendInput 发送相对鼠标移动"""

import json
import time
import ctypes

import pyautogui
from pynput import keyboard as pynput_keyboard

from config import SCREEN_W, SCREEN_H, CENTER_RESET_DELAY_MS

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# --- SendInput for relative mouse movement ---
user32 = ctypes.windll.user32
MOUSEEVENTF_MOVE = 0x0001


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", ctypes.c_long),
        ("dy", ctypes.c_long),
        ("mouseData", ctypes.c_ulong),
        ("dwFlags", ctypes.c_ulong),
        ("time", ctypes.c_ulong),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("mi", MOUSEINPUT)]
    _anonymous_ = ("_input",)
    _fields_ = [
        ("type", ctypes.c_ulong),
        ("_input", _INPUT),
    ]


def send_mouse_move(dx, dy):
    """用 SendInput 发送相对鼠标移动（游戏能捕获的原始移动）。"""
    inp = INPUT()
    inp.type = 0  # INPUT_MOUSE
    inp.mi.dx = dx
    inp.mi.dy = dy
    inp.mi.dwFlags = MOUSEEVENTF_MOVE
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(inp))


class Player:

    def __init__(self):
        self._center_x = SCREEN_W // 2
        self._center_y = SCREEN_H // 2
        self._kb_controller = pynput_keyboard.Controller()
        self.stopped = False

    def load(self, filepath: str) -> dict:
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[回放] 已加载 {filepath}，共 {len(data['events'])} 个事件")
        return data

    def split_phases(self, data: dict) -> dict:
        """根据 phase_marker 将事件分为 p1/p2/p3 三段，并裁剪 P1 末尾空白。"""
        events = data["events"]
        p2_idx = len(events)
        p3_idx = len(events)

        for i, ev in enumerate(events):
            if ev["type"] == "phase_marker":
                if ev["phase"] == 2 and p2_idx == len(events):
                    p2_idx = i
                elif ev["phase"] == 3 and p3_idx == len(events):
                    p3_idx = i

        # 裁剪 P1：找到最后一个实际操作事件，去掉后面的等待
        p1_events = events[:p2_idx]
        last_action = -1
        for i, ev in enumerate(p1_events):
            if ev["type"] in ("mouse_click", "key_down", "key_up"):
                last_action = i
        if last_action >= 0:
            p1_events = p1_events[:last_action + 1]

        phases = {
            "p1": p1_events,
            "p2": events[p2_idx:p3_idx],
            "p3": events[p3_idx:],
        }
        print(f"[回放] 分段: P1={len(phases['p1'])} P2={len(phases['p2'])} P3={len(phases['p3'])}")
        return phases

    def play_segment(self, events: list, center_reset: bool):
        """回放一段事件。center_reset=True 时用 SendInput 发送相对移动。"""
        if not events:
            return

        self.stopped = False
        t_offset = events[0]["t"]
        start_ns = time.perf_counter_ns()

        for event in events:
            if self.stopped:
                print("[回放] 已停止")
                return

            t_rel = event["t"] - t_offset
            target_ns = start_ns + int(t_rel * 1_000_000)
            while time.perf_counter_ns() < target_ns:
                pass

            etype = event["type"]

            if etype == "mouse_delta":
                # Raw Input delta → SendInput 相对移动
                send_mouse_move(event["dx"], event["dy"])

            elif etype == "mouse_move":
                if center_reset:
                    # 兼容旧格式：center-reset + delta
                    pyautogui.moveTo(self._center_x, self._center_y, _pause=False)
                    time.sleep(CENTER_RESET_DELAY_MS / 1000.0)
                    dx = event["x"] - self._center_x
                    dy = event["y"] - self._center_y
                    send_mouse_move(dx, dy)
                else:
                    pyautogui.moveTo(event["x"], event["y"], _pause=False)

            elif etype == "mouse_click":
                btn = "left" if event.get("button", "left") == "left" else "right"
                pyautogui.click(event["x"], event["y"], button=btn, _pause=False)

            elif etype == "key_down":
                self._press_key(event["key"], True)

            elif etype == "key_up":
                self._press_key(event["key"], False)

    def _press_key(self, key: str, press: bool):
        if len(key) == 1:
            k = pynput_keyboard.KeyCode.from_char(key)
        else:
            k = getattr(pynput_keyboard.Key, key, None)
            if k is None:
                k = pynput_keyboard.KeyCode.from_char(key)
        if press:
            self._kb_controller.press(k)
        else:
            self._kb_controller.release(k)

    def stop(self):
        self.stopped = True

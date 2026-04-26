"""录制器：144fps 捕获鼠标 delta（Raw Input）+ 键盘事件"""

import json
import time
import ctypes
import ctypes.wintypes
import threading
from datetime import datetime
from collections import deque

import pyautogui
from pynput import keyboard, mouse

from config import (
    SCREEN_W, SCREEN_H, RECORD_FPS, FRAME_INTERVAL,
    HOTKEY_PHASE2, HOTKEY_PHASE3, RECORDING_DIR,
)

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False

# --- Windows Raw Input 常量 ---
user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RIM_TYPEMOUSE = 0

WM_INPUT = 0x00FF
WM_DESTROY = 0x0002


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [
        ("dwType", ctypes.wintypes.DWORD),
        ("dwSize", ctypes.wintypes.DWORD),
        ("hDevice", ctypes.wintypes.HANDLE),
        ("wParam", ctypes.wintypes.WPARAM),
    ]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [
        ("usFlags", ctypes.c_ushort),
        ("usButtonFlags", ctypes.c_ushort),
        ("usButtonData", ctypes.c_ushort),
        ("ulRawButtons", ctypes.c_ulong),
        ("lLastX", ctypes.c_long),
        ("lLastY", ctypes.c_long),
        ("ulExtraInformation", ctypes.c_ulong),
    ]


class RAWINPUT(ctypes.Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("mouse", RAWMOUSE),
    ]


WNDPROC = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.wintypes.HWND,
                              ctypes.wintypes.UINT, ctypes.wintypes.WPARAM,
                              ctypes.wintypes.LPARAM)


class WNDCLASS(ctypes.Structure):
    _fields_ = [
        ("style", ctypes.wintypes.UINT),
        ("lpfnWndProc", WNDPROC),
        ("cbClsExtra", ctypes.c_int),
        ("cbWndExtra", ctypes.c_int),
        ("hInstance", ctypes.wintypes.HINSTANCE),
        ("hIcon", ctypes.wintypes.HANDLE),
        ("hCursor", ctypes.wintypes.HANDLE),
        ("hbrBackground", ctypes.wintypes.HANDLE),
        ("lpszMenuName", ctypes.wintypes.LPCWSTR),
        ("lpszClassName", ctypes.wintypes.LPCWSTR),
    ]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [
        ("usUsagePage", ctypes.c_ushort),
        ("usUsage", ctypes.c_ushort),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("hwndTarget", ctypes.wintypes.HWND),
    ]


def _raw_input_listener(delta_queue, running_flag):
    """后台线程：创建隐藏窗口，注册 Raw Input，接收鼠标 delta。"""
    h_instance = kernel32.GetModuleHandleW(None)

    wnd_class = WNDCLASS()
    def _wnd_proc(hwnd, msg, wp, lp):
        return user32.DefWindowProcW(
            ctypes.wintypes.HWND(hwnd),
            ctypes.wintypes.UINT(msg),
            ctypes.wintypes.WPARAM(wp),
            ctypes.wintypes.LPARAM(lp),
        )
    wnd_class.lpfnWndProc = WNDPROC(_wnd_proc)
    wnd_class.hInstance = h_instance
    wnd_class.lpszClassName = "RawInputCapture"

    atom = user32.RegisterClassW(ctypes.byref(wnd_class))
    hwnd = user32.CreateWindowExW(0, atom, "RawInputCapture", 0, 0, 0, 0, 0,
                                   None, None, h_instance, None)

    rid = RAWINPUTDEVICE()
    rid.usUsagePage = 0x01  # Generic Desktop
    rid.usUsage = 0x02      # Mouse
    rid.dwFlags = RIDEV_INPUTSINK
    rid.hwndTarget = hwnd
    user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid))

    msg = ctypes.wintypes.MSG()
    buf = ctypes.create_string_buffer(1024)

    while running_flag[0]:
        while user32.PeekMessageW(ctypes.byref(msg), hwnd, 0, 0, 1):
            if msg.message == WM_INPUT:
                size = ctypes.wintypes.UINT(0)
                user32.GetRawInputData(msg.lParam, RID_INPUT, None,
                                        ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER))
                if size.value > 0 and size.value <= 1024:
                    user32.GetRawInputData(msg.lParam, RID_INPUT, buf,
                                            ctypes.byref(size), ctypes.sizeof(RAWINPUTHEADER))
                    raw = ctypes.cast(buf, ctypes.POINTER(RAWINPUT)).contents
                    if raw.header.dwType == RIM_TYPEMOUSE:
                        dx = raw.mouse.lLastX
                        dy = raw.mouse.lLastY
                        if dx != 0 or dy != 0:
                            delta_queue.append((dx, dy))
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageW(ctypes.byref(msg))
        time.sleep(0.001)

    user32.DestroyWindow(hwnd)
    user32.UnregisterClassW(atom, h_instance)


class Recorder:
    """录制鼠标 delta（Raw Input）+ 键盘事件。"""

    def __init__(self):
        self.events = []
        self.recording = False
        self._start_time = 0
        self._keys_held = set()
        self._lock = threading.Lock()
        self._delta_queue = deque()
        self._running_flag = [False]

    def _now_ms(self) -> float:
        return (time.perf_counter_ns() - self._start_time) / 1_000_000

    def _add_event(self, event: dict):
        with self._lock:
            self.events.append(event)

    def _on_key_press(self, key):
        if not self.recording:
            return
        try:
            k = key.char
        except AttributeError:
            k = key.name

        if k == HOTKEY_PHASE2:
            self._add_event({"t": self._now_ms(), "type": "phase_marker", "phase": 2})
            print(f"  [标记] Phase 2 开始")
            return
        if k == HOTKEY_PHASE3:
            self._add_event({"t": self._now_ms(), "type": "phase_marker", "phase": 3})
            print(f"  [标记] Phase 3 开始")
            return

        if k not in self._keys_held:
            self._keys_held.add(k)
            self._add_event({"t": self._now_ms(), "type": "key_down", "key": k})

    def _on_key_release(self, key):
        if not self.recording:
            return
        try:
            k = key.char
        except AttributeError:
            k = key.name
        self._keys_held.discard(k)
        self._add_event({"t": self._now_ms(), "type": "key_up", "key": k})

    def _on_click(self, x, y, button, pressed):
        if not self.recording:
            return
        if pressed:
            self._add_event({
                "t": self._now_ms(),
                "type": "mouse_click",
                "x": x, "y": y,
                "button": "left" if button == mouse.Button.left else "right",
            })

    def _record_loop(self):
        """144fps 主循环：从 Raw Input 队列取出 delta 并记录。"""
        while self.recording:
            frame_start = time.perf_counter_ns()

            # 消费所有累积的 raw input delta
            while self._delta_queue:
                dx, dy = self._delta_queue.popleft()
                self._add_event({
                    "t": self._now_ms(),
                    "type": "mouse_delta",
                    "dx": dx,
                    "dy": dy,
                })

            elapsed = (time.perf_counter_ns() - frame_start) / 1_000_000_000
            sleep_time = FRAME_INTERVAL - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        self.events = []
        self._keys_held = set()
        self._delta_queue = deque()
        self._start_time = time.perf_counter_ns()
        self.recording = True
        self._running_flag[0] = True

        # Raw Input 监听线程
        self._raw_thread = threading.Thread(
            target=_raw_input_listener,
            args=(self._delta_queue, self._running_flag),
            daemon=True,
        )
        self._raw_thread.start()

        # 键盘监听
        self._kb_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._kb_listener.start()

        # 鼠标点击监听
        self._mouse_listener = mouse.Listener(on_click=self._on_click)
        self._mouse_listener.start()

        # 录制主循环
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

        print(f"[录制] 已开始 ({RECORD_FPS}fps, Raw Input)")
        print(f"  按 {HOTKEY_PHASE2.upper()} 标记跑酷开始")
        print(f"  按 {HOTKEY_PHASE3.upper()} 标记结算开始")

    def stop(self) -> dict:
        self.recording = False
        self._running_flag[0] = False
        self._kb_listener.stop()
        self._mouse_listener.stop()

        data = {
            "version": 3,
            "screen": [SCREEN_W, SCREEN_H],
            "fps": RECORD_FPS,
            "created": datetime.now().isoformat(),
            "events": self.events,
        }

        print(f"[录制] 已停止，共 {len(self.events)} 个事件")
        return data

    def save(self, data: dict, filepath: str = None):
        import os
        if filepath is None:
            os.makedirs(RECORDING_DIR, exist_ok=True)
            filepath = f"{RECORDING_DIR}/cloud_run_{int(time.time())}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[录制] 已保存到 {filepath}")
        return filepath

"""录制器：144fps 捕获鼠标 delta + 键盘事件"""

import json
import time
import threading
from datetime import datetime

import pyautogui
from pynput import keyboard

from config import (
    SCREEN_W, SCREEN_H, RECORD_FPS, FRAME_INTERVAL,
    CENTER_RESET_DELAY_MS, RECORDING_DIR,
)

# 禁用 pyautogui 的安全暂停和失败保护（游戏自动化场景）
pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


class Recorder:
    """录制鼠标移动（相对屏幕中心的 delta）和键盘事件。"""

    def __init__(self):
        self.events = []
        self.recording = False
        self._start_time = 0
        self._center_x = SCREEN_W // 2
        self._center_y = SCREEN_H // 2
        self._keys_held = set()
        self._lock = threading.Lock()

    def _now_ms(self) -> float:
        """返回相对于录制开始的毫秒数。"""
        return (time.perf_counter_ns() - self._start_time) / 1_000_000

    def _add_event(self, event: dict):
        """线程安全地添加事件。"""
        with self._lock:
            self.events.append(event)

    def _on_key_press(self, key):
        if not self.recording:
            return
        try:
            k = key.char
        except AttributeError:
            k = key.name
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

    def _record_loop(self):
        """144fps 主录制循环。"""
        while self.recording:
            frame_start = time.perf_counter_ns()

            # 1. 将鼠标移到屏幕中心
            pyautogui.moveTo(self._center_x, self._center_y, _pause=False)

            # 2. 短暂等待让游戏引擎读取中心位置
            time.sleep(CENTER_RESET_DELAY_MS / 1000.0)

            # 3. 捕获当前鼠标位置，计算 delta
            mx, my = pyautogui.position()
            dx = mx - self._center_x
            dy = my - self._center_y

            # 只记录有实际移动的事件
            if dx != 0 or dy != 0:
                self._add_event({
                    "t": self._now_ms(),
                    "type": "mouse_move",
                    "dx": dx,
                    "dy": dy,
                })

            # 4. 帧率控制：等待到下一帧
            elapsed = (time.perf_counter_ns() - frame_start) / 1_000_000_000
            sleep_time = FRAME_INTERVAL - elapsed
            if sleep_time > 0:
                time.sleep(sleep_time)

    def start(self):
        """开始录制。"""
        self.events = []
        self._keys_held = set()
        self._start_time = time.perf_counter_ns()
        self.recording = True

        # 启动键盘监听
        self._listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._listener.start()

        # 启动录制循环（后台线程）
        self._thread = threading.Thread(target=self._record_loop, daemon=True)
        self._thread.start()

        print(f"[录制] 已开始 ({RECORD_FPS}fps)")

    def stop(self) -> dict:
        """停止录制，返回录制数据。"""
        self.recording = False
        self._listener.stop()

        data = {
            "version": 1,
            "screen": [SCREEN_W, SCREEN_H],
            "fps": RECORD_FPS,
            "created": datetime.now().isoformat(),
            "events": self.events,
        }

        print(f"[录制] 已停止，共 {len(self.events)} 个事件")
        return data

    def save(self, data: dict, filepath: str = None):
        """保存录制数据到 JSON 文件。"""
        import os
        if filepath is None:
            os.makedirs(RECORDING_DIR, exist_ok=True)
            filepath = f"{RECORDING_DIR}/cloud_run_{int(time.time())}.json"

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"[录制] 已保存到 {filepath}")
        return filepath

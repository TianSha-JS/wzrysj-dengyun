"""回放器：精确回放录制的鼠标 delta + 键盘事件"""

import json
import time

import pyautogui
from pynput import keyboard as pynput_keyboard

from config import SCREEN_W, SCREEN_H, CENTER_RESET_DELAY_MS

pyautogui.PAUSE = 0
pyautogui.FAILSAFE = False


class Player:
    """回放录制文件中的事件序列。"""

    def __init__(self):
        self._center_x = SCREEN_W // 2
        self._center_y = SCREEN_H // 2
        self._kb_controller = pynput_keyboard.Controller()
        self.stopped = False

    def load(self, filepath: str) -> dict:
        """加载录制文件。"""
        with open(filepath, "r", encoding="utf-8") as f:
            data = json.load(f)
        print(f"[回放] 已加载 {filepath}，共 {len(data['events'])} 个事件")
        return data

    def play(self, data: dict):
        """回放录制数据中的所有事件。"""
        events = data["events"]
        if not events:
            print("[回放] 无事件")
            return

        print(f"[回放] 开始回放...")
        self.stopped = False
        start_ns = time.perf_counter_ns()

        for event in events:
            if self.stopped:
                print("[回放] 已停止")
                return

            # 精确等待到事件时间点
            target_ns = start_ns + int(event["t"] * 1_000_000)
            while time.perf_counter_ns() < target_ns:
                # 自旋等待，精度最高
                pass

            self._execute_event(event)

        print("[回放] 完成")

    def _execute_event(self, event: dict):
        """执行单个事件。"""
        etype = event["type"]

        if etype == "mouse_move":
            # 先归位到屏幕中心
            pyautogui.moveTo(self._center_x, self._center_y, _pause=False)
            time.sleep(CENTER_RESET_DELAY_MS / 1000.0)
            # 再施加 delta
            pyautogui.moveRel(event["dx"], event["dy"], _pause=False)

        elif etype == "key_down":
            key = event["key"]
            if len(key) == 1:
                self._kb_controller.press(pynput_keyboard.KeyCode.from_char(key))
            else:
                special = getattr(pynput_keyboard.Key, key, None)
                self._kb_controller.press(special or pynput_keyboard.KeyCode.from_char(key))

        elif etype == "key_up":
            key = event["key"]
            if len(key) == 1:
                self._kb_controller.release(pynput_keyboard.KeyCode.from_char(key))
            else:
                special = getattr(pynput_keyboard.Key, key, None)
                self._kb_controller.release(special or pynput_keyboard.KeyCode.from_char(key))

        elif etype == "mouse_click":
            pyautogui.click(event["x"], event["y"], _pause=False)

    def stop(self):
        """停止回放。"""
        self.stopped = True

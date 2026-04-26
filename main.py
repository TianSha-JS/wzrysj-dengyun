"""主入口：热键监听 + 三阶段串联"""

import sys
import time
import threading

import pyautogui
from pynput import keyboard

from config import (
    PHASE1_CLICKS, PHASE3_CLICKS,
    PHASE1_LOAD_WAIT, PHASE3_LOAD_WAIT, PHASE2_SETTLE_WAIT,
    HOTKEY_RECORD, HOTKEY_RUN, HOTKEY_STOP,
    DEFAULT_RECORDING,
)
from recorder import Recorder
from player import Player

pyautogui.PAUSE = 0.1
pyautogui.FAILSAFE = False


class Automation:
    """登云拾穗自动化主控。"""

    def __init__(self):
        self.recorder = Recorder()
        self.player = Player()
        self._running = False

    def phase1_enter(self):
        """Phase 1: 从主界面进入小游戏。"""
        print("[Phase 1] 进入小游戏...")
        for x, y, desc in PHASE1_CLICKS:
            pyautogui.click(x, y)
            print(f"  点击: {desc} ({x}, {y})")
            time.sleep(PHASE1_LOAD_WAIT)
        print("[Phase 1] 完成")

    def phase3_exit(self):
        """Phase 3: 退出回到主界面。"""
        print("[Phase 3] 退出小游戏...")
        time.sleep(PHASE3_LOAD_WAIT)
        for x, y, desc in PHASE3_CLICKS:
            pyautogui.click(x, y)
            print(f"  点击: {desc} ({x}, {y})")
            time.sleep(0.5)
        print("[Phase 3] 完成")

    def run_full(self, recording_path: str = None):
        """执行完整的三阶段自动化。"""
        if recording_path is None:
            recording_path = DEFAULT_RECORDING

        self._running = True
        print(f"\n{'='*50}")
        print(f"登云拾穗自动化 - 开始运行")
        print(f"{'='*50}\n")

        # Phase 1
        if not self._running:
            return
        self.phase1_enter()

        # Phase 2: 回放跑酷
        if not self._running:
            return
        print("\n[Phase 2] 开始跑酷回放...")
        time.sleep(PHASE2_SETTLE_WAIT)
        data = self.player.load(recording_path)
        self.player.play(data)

        # Phase 3
        if not self._running:
            return
        self.phase3_exit()

        print(f"\n{'='*50}")
        print(f"登云拾穗自动化 - 运行完成")
        print(f"{'='*50}\n")

    def stop(self):
        """紧急停止。"""
        self._running = False
        self.recorder.recording = False
        self.player.stop()
        print("[紧急停止]")


def main():
    automation = Automation()

    def on_press(key):
        try:
            k = key.name if hasattr(key, 'name') else key.char
        except AttributeError:
            return

        if k == HOTKEY_RECORD:
            if not automation.recorder.recording:
                automation.recorder.start()
            else:
                data = automation.recorder.stop()
                automation.recorder.save(data)

        elif k == HOTKEY_RUN:
            if not automation._running:
                threading.Thread(
                    target=automation.run_full, daemon=True
                ).start()

        elif k == HOTKEY_STOP:
            automation.stop()

    print("=" * 50)
    print("登云拾穗自动化脚本")
    print("=" * 50)
    print(f"  F9  = 开始/停止录制")
    print(f"  F10 = 开始自动运行")
    print(f"  F12 = 紧急停止")
    print("=" * 50)
    print("等待操作...\n")

    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()


if __name__ == "__main__":
    main()

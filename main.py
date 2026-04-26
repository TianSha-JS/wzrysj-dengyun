"""主入口：热键监听 + 图像检测驱动回放"""

import os
import sys
import time
import threading

import pyautogui
from pynput import keyboard

from config import (
    HOTKEY_RECORD, HOTKEY_RUN, HOTKEY_STOP, HOTKEY_EXIT,
    DEFAULT_RECORDING, RUN_COUNT, RUN_INTERVAL,
    IMG_SEG1, IMG_SEG2, IMG_CONFIDENCE, IMG_CHECK_INTERVAL, IMG_TIMEOUT,
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

    def wait_for_image(self, image_path: str, desc: str) -> bool:
        """等待屏幕上出现指定图片。"""
        print(f"  等待检测: {desc} ...")
        start = time.time()
        while self._running and (time.time() - start) < IMG_TIMEOUT:
            try:
                loc = pyautogui.locateOnScreen(image_path, confidence=IMG_CONFIDENCE)
                if loc is not None:
                    print(f"  检测到: {desc}")
                    return True
            except Exception:
                pass
            time.sleep(IMG_CHECK_INTERVAL)
        print(f"  超时未检测到: {desc}")
        return False

    def _run_once(self, phases, run_num):
        """执行一局。"""
        print(f"\n--- 第 {run_num} 局 ---\n")

        # Phase 1: 回放 UI 点击（进游戏）
        print("[Phase 1] 进入游戏...")
        self.player.play_segment(phases["p1"], center_reset=False)

        # 等待加载完成
        if not self.wait_for_image(IMG_SEG1, "加载完成"):
            return False

        # Phase 2: 回放跑酷
        print("[Phase 2] 跑酷...")
        time.sleep(0.5)
        self.player.play_segment(phases["p2"], center_reset=True)

        # 等待结算画面
        if not self.wait_for_image(IMG_SEG2, "结算画面"):
            return False

        # Phase 3: 回放退出操作
        print("[Phase 3] 退出...")
        time.sleep(0.5)
        self.player.play_segment(phases["p3"], center_reset=False)

        return True

    def run_full(self, recording_path: str = None):
        if recording_path is None:
            recording_path = DEFAULT_RECORDING

        if not os.path.exists(recording_path):
            print(f"[错误] 找不到录制文件: {recording_path}")
            print(f"  请先按 F10 录制一局")
            return

        self._running = True
        print(f"\n{'='*50}")
        print(f"登云拾穗自动化 - 连续运行 {RUN_COUNT} 局")
        print(f"{'='*50}")

        data = self.player.load(recording_path)
        phases = self.player.split_phases(data)

        for i in range(1, RUN_COUNT + 1):
            if not self._running:
                break

            if not self._run_once(phases, i):
                break

            # 不是最后一局则等待
            if i < RUN_COUNT and self._running:
                print(f"\n等待 {RUN_INTERVAL} 秒后开始下一局...")
                end = time.time() + RUN_INTERVAL
                while time.time() < end and self._running:
                    time.sleep(0.1)

        print(f"\n{'='*50}")
        print(f"登云拾穗自动化 - 全部完成")
        print(f"{'='*50}\n")

    def stop(self):
        self._running = False
        self.recorder.recording = False
        self.player.stop()
        print("[紧急停止]")


def main():
    automation = Automation()
    ctrl_held = {"ctrl_l": False, "ctrl_r": False}

    def on_press(key):
        nonlocal ctrl_held
        try:
            k = key.name if hasattr(key, 'name') else key.char
        except AttributeError:
            return

        if k in ("ctrl_l", "ctrl_r"):
            ctrl_held[k] = True
            return

        if k == HOTKEY_EXIT[1] and (ctrl_held["ctrl_l"] or ctrl_held["ctrl_r"]):
            print("[退出]")
            automation.stop()
            sys.exit(0)

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

    def on_release(key):
        nonlocal ctrl_held
        try:
            k = key.name if hasattr(key, 'name') else key.char
        except AttributeError:
            return
        if k in ("ctrl_l", "ctrl_r"):
            ctrl_held[k] = False

    print("=" * 50)
    print("登云拾穗自动化脚本")
    print("=" * 50)
    print(f"  F7       = 录制中标记：跑酷开始")
    print(f"  F8       = 录制中标记：结算开始")
    print(f"  F10      = 开始/停止录制")
    print(f"  F11      = 开始自动运行")
    print(f"  F12      = 紧急停止")
    print(f"  Ctrl+F12 = 退出程序")
    print("=" * 50)
    print("等待操作...\n")

    with keyboard.Listener(on_press=on_press, on_release=on_release) as listener:
        listener.join()


if __name__ == "__main__":
    main()

"""坐标拾取工具：鼠标移到目标位置，按空格记录坐标，按 Esc 退出"""

from pynput import keyboard, mouse

positions = []
mouse_pos = [0, 0]


def on_move(x, y):
    mouse_pos[0] = x
    mouse_pos[1] = y


def on_press(key):
    if key == keyboard.Key.space:
        pos = (mouse_pos[0], mouse_pos[1])
        positions.append(pos)
        print(f"  #{len(positions)} 记录: ({pos[0]}, {pos[1]})")
    elif key == keyboard.Key.esc:
        print("\n结果汇总:")
        for i, (x, y) in enumerate(positions):
            print(f"  #{i+1}: ({x}, {y})")
        print("\n复制到 config.py 的 PHASE1_CLICKS 中即可")
        return False


print("=" * 40)
print("坐标拾取工具")
print("=" * 40)
print("  移动鼠标 → 按空格记录坐标")
print("  按 Esc 退出并汇总")
print("=" * 40)

ml = mouse.Listener(on_move=on_move)
ml.start()

with keyboard.Listener(on_press=on_press) as kl:
    kl.join()

ml.stop()

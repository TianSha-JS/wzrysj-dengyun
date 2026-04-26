"""登云拾穗自动化脚本 - 配置文件"""

# 屏幕分辨率（全屏模式）
SCREEN_W = 1920
SCREEN_H = 1080

# 录制帧率
RECORD_FPS = 144
FRAME_INTERVAL = 1.0 / RECORD_FPS  # ~6.94ms

# 热键
HOTKEY_RECORD = "f10"          # 开始/停止录制
HOTKEY_RUN = "f11"             # 开始自动运行
HOTKEY_STOP = "f12"            # 紧急停止
HOTKEY_PHASE2 = "f7"           # 录制中标记跑酷开始
HOTKEY_PHASE3 = "f8"           # 录制中标记结算开始
HOTKEY_EXIT = ("ctrl", "f12")  # Ctrl+F12 退出程序

# 自动运行
RUN_COUNT = 25             # 连续运行次数
RUN_INTERVAL = 20          # 两次运行间隔（秒）

# 录制文件
RECORDING_DIR = "recordings"
DEFAULT_RECORDING = "recordings/cloud_run_1.json"

# 鼠标中心复位等待时间（毫秒）
CENTER_RESET_DELAY_MS = 1

# 图像检测
IMG_SEG1 = "img/seg1.png"  # 加载完成画面
IMG_SEG2 = "img/seg2.png"  # 结算画面（本次拾穗已结束）
IMG_CONFIDENCE = 0.8
IMG_CHECK_INTERVAL = 0.5   # 检测间隔（秒）
IMG_TIMEOUT = 60            # 最大等待时间（秒）

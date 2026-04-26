"""登云拾穗自动化脚本 - 配置文件"""

# 屏幕分辨率（全屏模式）
SCREEN_W = 1920
SCREEN_H = 1080

# 录制帧率
RECORD_FPS = 144
FRAME_INTERVAL = 1.0 / RECORD_FPS  # ~6.94ms

# Phase 1: 进入小游戏的 UI 点击坐标 (x, y, 描述)
# 用户需根据实际游戏界面填写
PHASE1_CLICKS = [
    (960, 540, "活动入口"),
    (960, 540, "登云拾穗"),
    (960, 540, "开始"),
]

# Phase 3: 退出回到主界面的 UI 点击坐标
PHASE3_CLICKS = [
    (960, 540, "确认返回"),
]

# 等待时间（秒）
PHASE1_LOAD_WAIT = 3.0
PHASE3_LOAD_WAIT = 2.0
PHASE2_SETTLE_WAIT = 1.0  # Phase 2 开始前等待游戏稳定

# 热键
HOTKEY_RECORD = "f9"
HOTKEY_RUN = "f10"
HOTKEY_STOP = "f12"

# 录制文件
RECORDING_DIR = "recordings"
DEFAULT_RECORDING = "recordings/cloud_run_1.json"

# 鼠标中心复位等待时间（毫秒），让游戏引擎读取到中心位置
CENTER_RESET_DELAY_MS = 1

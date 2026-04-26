# 登云拾穗自动化脚本

王者荣耀世界「登云拾穗」跑酷小游戏自动化工具。

## 用前须知

默认刷第三关，需传送到登云拾穗npc面前。
第一次使用需与npc对话，并将小游戏选关界面切换至第一页，然后关闭。

## 安装

```bash
pip install -r requirements.txt
```

依赖：`pynput`、`pyautogui`、`opencv-python`

## 文件结构

```
├── main.py            # 主入口，热键控制
├── recorder.py        # 144fps 录制器（Raw Input + 键盘 + 点击）
├── player.py          # 回放器（SendInput 相对移动）
├── config.py          # 配置：分辨率、热键、运行次数等
├── get_pos.py         # 坐标拾取工具
├── img/
│   ├── seg1.png       # 加载完成画面截图
│   └── seg2.png       # 结算画面截图
├── recordings/        # 录制文件存放目录
└── requirements.txt
```

## 使用

```bash
python main.py
```

已完成录制可直接使用，F11一键启动。

| 按键 | 操作 |
|------|------|
| F10 | 开始/停止录制 |
| F11 | 开始自动运行（默认 25 局） |
| F12 | 紧急停止 |
| Ctrl+F12 | 退出程序 |
| F7 | 录制中标记：跑酷开始 |
| F8 | 录制中标记：结算开始 |

## 配置

编辑 `config.py`：

```python
SCREEN_W = 1920          # 屏幕宽度
SCREEN_H = 1080          # 屏幕高度
RUN_COUNT = 25           # 连续运行次数
RUN_INTERVAL = 20        # 两局间隔（秒）
IMG_CONFIDENCE = 0.8     # 图像匹配置信度
```

# tb3_tools —— TurtleBot3 仿真小车工具链（第 3 章三级项目）

> 状态：**准备阶段**。前置依赖与功能包骨架已就绪，Launch / tf / rqt / rosbag 的具体实现尚未编写，
> 仿真也尚未启动。待办清单见文末「当前进度」。

本项目按《第 3 章项目任务书：TurtleBot3 仿真小车工具链》完成，目标是交出一个
**可启动、可观察、可记录、可复现**的 ROS 2 仿真小车工程。

## 一、运行环境

| 项目 | 版本 / 取值 |
| --- | --- |
| 操作系统 | Ubuntu 24.04.5 LTS（内核 6.8.0-139-generic） |
| ROS 2 | Jazzy |
| 仿真器 | Gazebo Sim（Harmonic，随 `ros-jazzy-ros-gz` 安装） |
| 机器人模型 | `turtlebot3_gazebo` 的 **TurtleBot3 Waffle Pi**（`TURTLEBOT3_MODEL=waffle_pi`） |
| 启动文件 | `turtlebot3_world.launch.py` |
| 工作空间 | `~/task1_ws`（本项目专用，与其它工程隔离） |

**Jazzy 注意事项**：本模型的 `/cmd_vel` 类型是 `geometry_msgs/msg/TwistStamped`，
不是旧版教材里的 `Twist`。发布速度前务必用 `ros2 topic type /cmd_vel` 核对。

## 二、目录结构

```
task1/
├── README.md                    本文件
├── 03_第3章_ROS2常用工具_三级项目任务书.md   任务书原文
├── src/
│   └── tb3_tools/               本项目功能包（ament_python）
│       ├── package.xml
│       ├── setup.py / setup.cfg
│       ├── resource/tb3_tools
│       ├── tb3_tools/            Python 节点
│       │   ├── image_monitor.py          图像帧率监测（进阶版）
│       │   ├── static_tf_broadcaster.py  静态 tf：base_link -> inspection_point（进阶版）
│       │   ├── dynamic_tf_broadcaster.py 动态 tf：odom -> moving_target（进阶版）
│       │   └── tf_listener.py            距离监听（进阶版）
│       ├── launch/
│       │   ├── basic.launch.py       基础版顶层 Launch
│       │   ├── integrated.launch.py  进阶版顶层 Launch
│       │   └── bringup.launch.py     挑战版入口（含故障切换 / 离线回放）
│       ├── rviz/basic.rviz       RViz 配置（Fixed Frame: odom）
│       └── config/params.yaml    参数默认值
├── docs/                        证据材料（截图、坐标系树、bag info、故障分析报告）
└── scripts/                     驱动虚拟机做前置/验证的运维脚本
```

## 三、构建与启动

```bash
# 每次新终端
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=waffle_pi

# 构建
cd ~/task1_ws
colcon build --symlink-install
source install/setup.bash

# 启动（实现完成后可用）
ros2 launch tb3_tools basic.launch.py
```

> 具体命令在各级功能实现后于此处补全（含 bag 录制/回放、故障切换、rqt 使用方式）。

## 四、当前进度

已完成（准备阶段）：

- [x] 环境勘察：确认 Ubuntu 24.04 + ROS 2 Jazzy，核对已装/缺失依赖
- [x] 安装前置依赖：`ros-jazzy-ros-gz`、`ros-jazzy-turtlebot3`、`ros-jazzy-turtlebot3-gazebo`
      （`rqt-common-plugins`、`tf2-tools`、`colcon`、`git` 为已装）
- [x] 新建独立工作空间 `~/task1_ws`（不与其它工程共用）
- [x] 建立功能包骨架 `tb3_tools`（元数据、目录结构、节点与 Launch 占位文件、参数默认值）
- [x] 骨架编译通过，确认工具链可用

**git 仓库：尚未建立。** 起初在客户机 `~/task1_ws` 建过一次并提交了骨架，
经确认该位置不可用，已整体删除（`rm -rf ~/task1_ws/.git`），工作空间与功能包文件全部保留。
任务书要求 git 提交记录，仓库位置待指定后再建。

待完成（任务本体，尚未执行）：

- [ ] 基础版 1：实现 `basic.launch.py`（包含仿真 + 启动 RViz + `use_sim_time` + 加载 `basic.rviz`）
- [ ] 基础版 2：键盘操控小车，用 `topic list -t` / `hz` 核实 `/camera/image_raw`、`/odom` 有数据
- [ ] 基础版 3：`view_frames` 导出坐标系树；`tf2_echo` 查询两组关系并解释动静之分
- [ ] 基础版 4：RViz 里配好 TF / LaserScan / Image（Fixed Frame = `odom`），逐项检查 Status
- [ ] 基础版 5：rqt 的 Node Graph 与 Image View
- [ ] 基础版 6：录制 `bags/basic`，`ros2 bag info` 核对四个话题非零；停仿真后仅开 RViz 回放
- [ ] 基础版 7：git 两次有意义提交（可启动版本 / 可视化与数据验证版本）
- [ ] 进阶版：图像监测节点 + 参数与重映射验证；静态/动态 tf 广播器；tf 监听与异常处理；rqt Plot
- [ ] 挑战版：两种可切换故障、离线复现、`bringup.launch.py`、故障分析报告、git 分支

## 五、必须回答的三个问题（先占位，实现阶段补答案）

1. Gazebo、RViz 和 rqt 在本项目中分别负责什么？
2. `odom → base_footprint` 与 `base_link → camera_rgb_frame` 为什么分别属于动态和静态关系？
3. rosbag 能回放什么，不能直接恢复什么？

## 六、AI 协作记录

按任务书要求，交互记录写在 `AI_协作记录.md`，至少两条真正影响实现的交互
（问题 → AI 建议 → 我执行的命令/观察结果 → 保留或修改的理由）。

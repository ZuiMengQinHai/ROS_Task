# tb3_tools —— TurtleBot3 仿真小车工具链（第 3 章三级项目）

> 状态：**基础版、进阶版、挑战版已完成**。
> 代码在 `src/tb3_tools/`，运行与观察步骤见
> [`docs/操作手册.md`](docs/操作手册.md)（基础版）与
> [`docs/操作手册_进阶与挑战.md`](docs/操作手册_进阶与挑战.md)（进阶 / 挑战），
> 证据材料在 `docs/evidence/`。

## 一、运行环境（实测）

| 项目 | 版本 / 取值 |
| --- | --- |
| 操作系统 | Ubuntu 24.04.5 LTS（内核 6.8.0-139-generic） |
| ROS 2 | Jazzy |
| 仿真器 | Gazebo Sim 8.15.0（Harmonic，随 `ros-jazzy-ros-gz` 安装） |
| 机器人模型 | `turtlebot3_gazebo` 的 **TurtleBot3 Waffle Pi**（`TURTLEBOT3_MODEL=waffle_pi`） |
| 仿真启动文件 | `turtlebot3_world.launch.py` |
| 工作空间 | `~/task1_ws`（本项目专用，与其它工程隔离） |
| 图形会话 | GNOME（Xorg），`DISPLAY=:0`，2299×1390，软件渲染 |

**Jazzy 注意事项**：本模型的 `/cmd_vel` 类型是 `geometry_msgs/msg/TwistStamped`，
不是旧教材里的 `Twist`。发速度前用 `ros2 topic type /cmd_vel` 核对。

**本机性能注意**：软件渲染下 Gazebo 的实时因子（RTF）只有 **0.07 ～ 0.1**，
即仿真 1 s 约等于墙钟 10 ～ 14 s。所以「每秒一个点」的曲线看着很稀疏是正常的；
bag 回放时用 `--rate 0.5` 可以把观测窗口拉长。

## 二、目录结构

```
ROS_Task/                        仓库根（本机 D:\pyproject\ROS_Task）
├── README.md                    本文件
├── AI_协作记录.md               任务书要求的 AI 协作记录
├── 03_第3章_ROS2常用工具_三级项目任务书.md
├── docs/
│   ├── 操作手册.md                    基础版：运行/观察/记录/提交
│   ├── 操作手册_进阶与挑战.md          进阶版 + 挑战版的操作清单
│   ├── 准备工作记录.md                前置依赖与骨架准备
│   ├── 进阶版说明.md                  静态/动态广播、参数、重映射的说明
│   ├── 故障分析报告.md                挑战版：两种故障的四栏记录（≤3 页）
│   └── evidence/                      证据：截图、坐标系树、命令输出、bag info
└── src/tb3_tools/               功能包（ament_python）
    ├── package.xml
    ├── setup.py / setup.cfg
    ├── resource/tb3_tools
    ├── tb3_tools/                Python 节点
    │   ├── image_monitor.py             图像帧率监测（进阶 2）
    │   ├── static_tf_broadcaster.py     静态 tf：base_link → inspection_point（进阶 3）
    │   ├── dynamic_tf_broadcaster.py    动态 tf：odom → moving_target（进阶 3）
    │   └── tf_listener.py               距离监听 + 异常处理（进阶 4）
    ├── launch/
    │   ├── basic.launch.py        基础版顶层 Launch
    │   ├── integrated.launch.py   进阶版顶层 Launch（参数 + 重映射 + 离线开关）
    │   └── bringup.launch.py      挑战版入口（mode × fault_mode）
    ├── rviz/
    │   ├── basic.rviz             基础版 RViz 配置（Fixed Frame: odom）
    │   └── integrated.rviz        进阶版 RViz 配置
    └── config/params.yaml         各节点参数默认值
```

> 客户机 `~/task1_ws` 是**编译与运行环境**（`src/tb3_tools` 由本仓库上传），
> 不放 git 仓库；版本管理统一在本机的 `ROS_Task` 仓库进行。

## 三、构建与启动

```bash
# 每次新终端
source /opt/ros/jazzy/setup.bash
export TURTLEBOT3_MODEL=waffle_pi

# 构建
cd ~/task1_ws
colcon build --symlink-install
source install/setup.bash

# 基础版（仿真 + RViz）
ros2 launch tb3_tools basic.launch.py

# 进阶版（仿真 + 图像监测 + 静态/动态 tf + 监听 + RViz）
ros2 launch tb3_tools integrated.launch.py
ros2 launch tb3_tools integrated.launch.py window_sec:=2.0     # 改统计窗口
```

### `integrated.launch.py` 参数

| 参数 | 默认 | 说明 |
| --- | --- | --- |
| `window_sec` | `5.0` | 帧率统计窗口（进阶版要求由 Launch 控制） |
| `image_topic` | `/camera/image_raw` | 图像监测节点的**话题重映射目标** |
| `target_frame` | `moving_target` | tf 监听查询的目标坐标系 |
| `sim` | `true` | 是否包含 Gazebo |
| `enable_tf` | `true` | 是否启动自编静态/动态广播器（离线回放必须 `false`） |
| `use_sim_time` | `true` | 使用 `/clock` |
| `rviz_config` | 本包 `rviz/integrated.rviz` | RViz 配置（不写死路径） |
| `headless` | `false` | `true` 则不启动 RViz |

## 四、挑战版：故障切换与离线回放

```bash
# 在线（正常 / 两种故障）
ros2 launch tb3_tools bringup.launch.py                     # 正常
ros2 launch tb3_tools bringup.launch.py fault_mode:=topic    # 话题故障
ros2 launch tb3_tools bringup.launch.py fault_mode:=frame    # 坐标故障

# 离线：只用数据包提供输入（不起 Gazebo、不起自编 tf 广播器）
ros2 bag play bags/final --clock --rate 0.5                  # 终端 R
ros2 launch tb3_tools bringup.launch.py mode:=offline        # 终端 A
ros2 launch tb3_tools bringup.launch.py mode:=offline fault_mode:=topic
ros2 launch tb3_tools bringup.launch.py mode:=offline fault_mode:=frame
```

| 故障 | 注入点 | 预期现象 |
| --- | --- | --- |
| `topic` | 监测节点重映射到 `/camera/image_missing`（无人发布） | 帧率恒 0；该话题只有订阅者没有发布者；日志反复告警；**RViz 图像仍正常** |
| `frame` | 监听节点 `target_frame:=moving_target_fault`（树里没有） | 距离发布 NaN、曲线断开；日志报 `LookupException`；`view_frames` 无此 frame |

修复 = 把 `fault_mode` 改回 `none`（不动 ROBOTIS 原始模型文件）。

## 五、数据包

| 文件 | 内容 | 说明 |
| --- | --- | --- |
| `bags/final`（客户机） | `/camera/image_raw`、`/odom`、`/tf`、`/tf_static`、`/clock`、`/robot_description` | 按要求「先开录制再启动」，因此 `latched` 话题也录到了；单独打包提交，不进 git |

**实测 `ros2 bag info`**（完整输出见 `docs/evidence/bag_info_final.txt`）：

| 项目 | 值 |
| --- | --- |
| 时长 | 87.76 s（10:00:51 → 10:02:18） |
| 消息数 | 6955 |
| `/camera/image_raw` | 179 |
| `/odom` | 297 |
| `/tf` | 533（含自己新增的 `odom → moving_target`） |
| `/tf_static` | 2（含 `base_link → inspection_point`） |
| `/robot_description` | 1 |
| `/clock` | 5943 |

录制顺序很关键：`/tf_static` 与 `/robot_description` 是 transient_local，
**录制器必须在发布者之前启动**，否则回放时会缺帧、tf 树断链（本次实测踩过，
`docs/evidence/verify_bag_tf.txt` 是「用这份包回放时 `base_link` 能否查到」的校验）。

## 六、三个必答题

**1. Gazebo、RViz 和 rqt 在本项目中分别负责什么？**

> Gazebo 是**数据源**：产生图像、`/odom`、`/scan`、`/tf`、`/clock`；
> RViz 是**几何与图像的场景化显示**：按保存好的配置把 TF、激光、图像一次画出来，便于交付与现场演示；
> rqt 是**调试台**：Node Graph 看节点/话题连接关系，Plot 看数值曲线，Image View 快速验证图像流。
> 一句话：Gazebo 产数据，RViz 看场景，rqt 查关系与曲线。

**2. `odom → base_footprint` 与 `base_link → camera_rgb_frame` 为什么分别属于动态和静态关系？**

> 前者由轮式里程计推算，车一动位姿就变，必须按频率持续广播（本机约 6 Hz），时间戳持续推进；
> 后者是相机在车体上的**安装位置**（本机 `base_link → camera_rgb_frame` 实测 `[0.076, 0.000, 0.093]`，
> 由 `camera_link`、`camera_rgb_frame` 两段固定关节叠加），机械上恒定，只发一次即可，
> 走 `/tf_static`（transient_local）。本工程新增的 `base_link → inspection_point`（静态）与
> `odom → moving_target`（动态）正好是一对对照。

**3. rosbag 能回放什么，不能直接恢复什么？**

> 能回放**当时发布过的 ROS 消息流**（图像、`/odom`、`/tf`、`/tf_static` 等），
> 因此只开 RViz 就能重现画面与坐标变换；用同一份包还能让自编节点的输出（帧率、距离）重现。
> 不能恢复 Gazebo 的**物理世界状态**（真实位姿、碰撞、摩擦、作用力），
> 也不能恢复没有录制的话题/服务调用；而故障本身是**配置**带来的，必须靠 `fault_mode` 注入才会出现。

## 七、当前进度

- [x] 环境勘察、依赖安装、工作空间与功能包骨架
- [x] **基础版**：`basic.launch.py`、键盘操控、话题核实、`view_frames`/`tf2_echo`、
      RViz Status、rqt Node Graph/Image View、`bags/basic` 录制与回放、git 两次提交
- [x] **进阶版**：
  - [x] `integrated.launch.py`（包含仿真 + RViz + `use_sim_time` + 自定义 rviz 配置，不写死路径）
  - [x] 图像帧率监测节点（`window_sec` 可配 + 发布 `std_msgs/Float64`）+ rqt Plot 曲线
  - [x] Launch 参数控制统计窗口、话题重映射（均实际运行验证）
  - [x] 静态广播器 `base_link → inspection_point`、动态广播器 `odom → moving_target`
  - [x] tf 监听节点（`lookup_transform` + 三类异常处理 + 距离话题）
  - [x] `view_frames` / `tf2_echo` / RViz TF 三种方式交叉验证
  - [x] rqt Node Graph 检查监测节点输入输出、rqt Plot 同时看帧率与距离
  - [x] 录制含图像/`odom`/`tf`/`tf_static` 的数据包，离线回放验证
  - [x] git 三次有意义提交
- [x] **挑战版**：
  - [x] `bringup.launch.py`：`mode:=sim|offline` × `fault_mode:=none|topic|frame`
  - [x] 两种可切换故障（话题故障、坐标故障），只作用于本包配置
  - [x] 四栏故障记录（`docs/故障分析报告.md`）
  - [x] 同一份数据包分别跑正常/故障配置并对比
  - [x] `README.md` 写明版本、模型、构建与启动、故障切换、预期话题、验收结果
  - [x] git 独立分支 `challenge/fault-injection` + 合并记录

## 八、证据索引（`docs/evidence/`）

| 文件 | 说明 |
| --- | --- |
| `frames_tree_online_sim.png|pdf` | 在线仿真的坐标系树（含 `inspection_point`、`moving_target`） |
| `frames_tree_offline_normal.*`、`frames_tree_topic_fault.*`、`frames_tree_frame_fault.*` | 离线三种配置下的坐标系树（对照「树里有没有那个 frame」） |
| `tf2_echo_*.txt` | 静态/动态关系的 `tf2_echo` 原始输出（含时间戳口径） |
| `offline_normal_evidence.txt`、`offline_topic_fault_evidence.txt`、`offline_frame_fault_evidence.txt` | 三种配置的节点/话题/参数/数值采样（含 `10.10`、`0.0`、`.nan` 对照） |
| `offline_*_node_logs.txt` | 两个自编节点在三种配置下的原始日志（告警原文） |
| `fix_param_check.txt` | 参数覆盖修正后的验证：`window_sec=2.0`、`target_frame=moving_target_fault`、距离 `.nan` |
| `shots/online_rviz_tf_laser_image.png` | 在线 RViz：TF + LaserScan + Image 同屏 |
| `shots/online_rqt_image_view.png` | rqt Image View 显示 `/camera/image_raw` |
| `shots/offline_rqt_plot_two_topics.png` | rqt Plot：`/image_monitor/fps/data` 与 `/tf_listener/distance/data` 两条曲线 |
| `shots/offline_rqt_graph.png` | rqt Node Graph（回放中的节点连接） |
| `shots/offline_normal_rviz.png`、`topic_fault_rviz.png`、`frame_fault_rviz.png` | 离线三种配置的 RViz 截图 |
| `bag_info_final.txt`、`verify_bag_tf.txt` | 数据包时长/计数；以及「这份包回放时 `base_link` 能否查到」的校验 |
| `topic_list_t_online.txt`、`topic_hz_online.txt`、`image_topic_info_verbose_online.txt` | 在线仿真的环境实测数据（话题清单、频率、QoS） |

> 说明：rqt 的两张截图取自界面采集成功的那一次运行（数值与三种配置的文本证据一致）；
> 三种配置的**权威证据是文本里的实测数值与节点日志**，不依赖截图。

## 九、AI 协作记录

见 [`AI_协作记录.md`](AI_协作记录.md)：记录了实现阶段真正影响实现的几次交互
（Launch 参数优先级、rosbag 录制顺序、tf 异常处理与 NaN 语义、rqt_graph 空白排查）。

## 十、提交记录

```
*   983a5d9 合并挑战版：故障注入与修复历史
|\
| * 7394dd6 挑战版：bringup.launch.py 故障模式（话题/坐标）与离线回放入口，附故障分析报告与证据
|/
* 658666d 进阶版：操作手册、进阶版说明、README 与证据（坐标系树 / RViz / rqt / bag info）
* feb06d9 进阶版：修正 Launch 参数覆盖（window_sec / target_frame 现在真正生效）
* 127b850 进阶版：实现图像帧率监测、静态/动态 tf 广播与 tf 监听节点，新增 integrated.launch.py
* a105c45 基础版：实现 basic.launch.py 与 basic.rviz，补充操作手册
* 3d8b11b 订正 README 与准备工作记录中的仓库信息
* cdb4e9c 初始化 tb3_tools 功能包骨架与工程结构
```

分支：`challenge/fault-injection`（故障注入与修复），已用 `--no-ff` 合并回 `main`。

远端仓库：<https://github.com/ZuiMengQinHai/ROS_Task.git>，已推送

- `main` —— 含合并提交 `983a5d9`、README 收尾提交
- `challenge/fault-injection` —— 独立分支（`7394dd6`），可直接开 PR 查看故障注入与修复的提交历史

> 数据包 `bags/final`（159 MB）按任务书要求**不进 git**，单独提交/作为课程平台附件。

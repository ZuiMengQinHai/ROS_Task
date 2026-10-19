# AI 协作记录

## 记录一：Launch 里覆盖参数不生效（`window_sec` 一直是 5.0）

| 栏目 | 内容 |
| --- | --- |
| 我的问题 | 要求「用 Launch 参数控制图像监测的统计窗口」，我写成 `Node(parameters=[params.yaml, {'window_sec': 2.0}])`，但 `ros2 param get /image_monitor window_sec` 一直是 5.0。 |
| AI 的建议 | 先看 launch 生成的临时参数文件长什么样；`launch_ros` 会把字典写成 `/**`（通配符）段落，而 `params.yaml` 里是按节点名 `image_monitor:` 写的，节点专属段落的优先级更高，所以覆盖失败。建议改用命令行 `--ros-args -p window_sec:=…`（优先级最高），或者直接把覆盖值也写进节点专属段落。 |
| 我的命令与观察 | `cat /tmp/launch_params_*` → 看到字典被写成了 `/**` 通配符段落；于是先按建议改用 `--ros-args -p window_sec:=…`，**单跑节点时有效**（`ros2 run … -p window_sec:=2.0` 日志变 2.0），但**经 Launch 启动后 `ros2 param get` 仍是 5.0**；挑战版的坐标故障同样注不进去（`target_frame` 一直是 `moving_target`，距离照常输出 1.234 m）。 |
| 采纳 / 修改及理由 | **最终改成「参数只留一处」**：`params.yaml` 里删掉 `window_sec` 与 `target_frame` 这两个键，默认值只留在节点代码里（5.0 / `moving_target`），Launch 用 `parameters=[params_file, {...}]` 传覆盖值。这样通配符段落是唯一来源，覆盖必然生效。理由：`-p` 与参数文件的交互在 Launch 组装的命令行里不可靠，而「同一参数只允许写在一个地方」是可验证、可解释的规则；改完后 `ros2 param get` 立刻显示 `window_sec=2.0`、`target_frame=moving_target_fault`，距离话题输出 `NaN`，日志出现 `LookupException`。 |

---

## 记录二：rosbag 录制顺序错了，导致离线回放 tf 树断链

| 栏目 | 内容 |
| --- | --- |
| 我的问题 | 先 `ros2 bag record` 还是先 `ros2 launch`？我先启动 Launch 再开录制，结果离线回放时 `tf2_echo base_link base_footprint` 报 `Invalid frame ID "base_link" ... frame does not exist`，监听节点一直 `LookupException`。 |
| AI 的建议 | `/tf_static`、`/robot_description` 是 transient_local（latched）话题，**发布者只在启动时发一次**；晚加入的订阅者拿不到历史值。要录到它们，必须在发布者之前启动录制器。建议顺序：开录制 → 启动 Launch → 让车动 → 停止录制；并且停止必须用 Ctrl+C 等它把 `metadata.yaml` 写出来，`kill -9` 会让整包作废。 |
| 我的命令与观察 | 对比两次包：`bags/integrated`（先启动后录）`ros2 bag info` 里 `/tf_static` 只有 2 条、回放时 `base_link` 不存在；改成先录后启动后，`/tf_static` 仍只有 2 条（正常，静态只发一两次），但回放里 `tf2_echo base_link base_footprint` 能正常出数。另外一次 `kill -9` 结束录制后 `ros2 bag info` 直接报 `Could not find metadata in bag directory`。 |
| 采纳 / 修改及理由 | **采纳**：操作手册里把「先退出仿真、先开录制、再启动顶层 Launch」写成硬性顺序；并把「Ctrl+C 后要等 `Recording stopped`」和「`bags/integrated2` 那次作废」写进常见问题，作为反面证据。 |

---

## 记录三：tf 查询失败时，距离话题该发 0 还是 NaN

| 栏目 | 内容 |
| --- | --- |
| 我的问题 | `lookup_transform` 失败时（frame 不存在 / 时间戳不匹配），距离话题应该发什么？最简单是发 0。 |
| AI 的建议 | 发 0 会被 rqt_plot 画成一条「距离=0」的真实曲线，看起来像"目标贴到车上了"，掩盖故障；发 `NaN` 在 rqt_plot / matplotlib 上表现为曲线**断开**，一眼能看出「这段没有数据」，再配合分类型的告警日志（Lookup / Connectivity / Extrapolation）就能定位。 |
| 我的命令与观察 | `fault_mode:=frame` 时观察 `/tf_listener/distance`：`data: .nan`；rqt_plot 上蓝线（帧率）正常、红线（距离）断开。日志里 `tf 查询失败 [LookupException]："moving_target_fault" passed to lookupTransform argument target_frame does not exist.` |
| 采纳 / 修改及理由 | **采纳**：`tf_listener.py` 在失败分支 `publish(Float64(data=nan))`，并把三类异常分别捕获、各带一句排查建议；恢复后补一条「查询恢复正常（此前连续错误 N 次）」日志，便于在 rqt Console 里圈出故障区间。 |

---

## 记录四：rqt_graph 全白、rqt_plot 没曲线

| 栏目 | 内容 |
| --- | --- |
| 我的问题 | 截图时 `rqt_graph` 画布全白；`rqt_plot` 窗口打开但一条曲线都没有（即使给了话题参数）。 |
| AI 的建议 | ① `rqt_graph` 在 `Nodes/Topics (active)` 模式下若勾着 `Hide: Dead sinks` 与 `Hide: Leaf topics`，本工程这种"一对一的叶子话题"会被全部隐藏，画布就空了；取消这两个勾，或切到 `Nodes only`。② `rqt_plot` 要写到**字段级**：`Float64` 的字段名是 `data`，只写话题名不画图。 |
| 我的命令与观察 | 取消两个勾后 `rqt_graph` 出图（能看到 `/tf_listener` 等节点）；`rqt_plot /image_monitor/fps/data /tf_listener/distance/data` 后图例出现两条线，蓝线约 10（fps）、红线约 1.2（m）。另外发现 `rqt_graph` 在 bag 播完之后会因为没有活动连接又变空，所以截图必须在回放过程中做。 |
| 采纳 / 修改及理由 | **采纳**：`bringup.launch.py` 里 rqt_plot 的参数写死成 `/image_monitor/fps/data`、`/tf_listener/distance/data`；操作手册里把这两个坑写成「截图要点」，并注明「截图要在回放进行中」。 |

---

## 记录五：停止方式不对会留下孤儿节点

| 栏目 | 内容 |
| --- | --- |
| 我的问题 | 用 `pkill -f 'ros2 launch tb3_tools'` 停 Launch 之后，再启动一次，`ros2 node list` 里出现两个 `/image_monitor`，`/tf_listener/distance` 的值在真值和 NaN 之间乱跳，rqt_plot 曲线完全没有参考价值。 |
| AI 的建议 | `ros2 launch` 只是启动器，被杀时子节点不保证收到退出信号，会变成孤儿继续跑；停的时候要连节点进程一起清，或者优先用 `Ctrl+C`（launch 会转发 SIGINT 并等待子进程退出）。启动前先 `ps` 确认没有残留，再开始采集证据。 |
| 我的命令与观察 | `ps -eo args \| grep -E 'tb3_tools/lib\|gz sim\|rviz2\|rqt'` 看到 5 个 `image_monitor`、5 个 `tf_listener`；`ros2 node list` 出现同名节点告警；清理后重新采集，数值才稳定（fps ~9、distance ~1.23 m）。 |
| 采纳 / 修改及理由 | **采纳**：所有验证脚本开头都先做一次彻底清理并打印「残留进程数=0」，操作手册的「怎么正确停」一节写成必做步骤。这条也进了故障排查表，因为"数值乱跳"最容易被误判成代码 bug。 |

---

## 附：准备阶段的环境问题（备查）

| 问题 | 现象 | 原因 | 处理 |
| --- | --- | --- | --- |
| apt 索引过期 | 安装 ROS 包时报 `404 Not Found` | 本地索引比软件源旧 | 先 `sudo apt update` |
| ROS CLI 发现图过期 | `ros2 topic list` 看不到实际在发布的话题 | `ros2` CLI 守护进程缓存 | `ros2 daemon stop && ros2 daemon start` |
| 软件渲染慢 | Gazebo 实时因子只有 0.07–0.1 | VMware 无 3D 加速（`VMware: No 3D enabled`） | 窗口别全屏；回放用 `--rate 0.5`；曲线稀疏属正常 |

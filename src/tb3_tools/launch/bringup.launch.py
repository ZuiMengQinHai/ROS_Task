"""挑战版入口 Launch —— 【挑战版 任务 1/4】骨架，尚未实现。

要求（来自任务书）：
  1. 加入故障模式选择，至少两种可切换故障：
       - 话题故障：把监测节点重映射到不存在的图像话题
       - 坐标故障：让监听节点查询不存在的目标 frame
     故障只作用于本包自己的配置或节点，不改 ROBOTIS 原始模型文件
  2. 提供离线分析启动方式：只用 rosbag 提供输入
     （回放时启动 图像监测 / tf 监听 / RViz / rqt，不启动 Gazebo 与自编 tf 广播器）
  3. 参数设计建议：
       fault_mode:=none|topic|frame
       use_sim_time:=true
"""


def generate_launch_description():
    raise NotImplementedError('TODO: bringup.launch.py 尚未实现（见任务书 挑战版 任务 1）')

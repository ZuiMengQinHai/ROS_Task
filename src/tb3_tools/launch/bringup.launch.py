#!/usr/bin/env python3
"""挑战版入口 Launch：故障模式切换 + 离线（rosbag）分析入口。

对应任务书 挑战版 任务 1、4。在进阶版（integrated.launch.py）之上只多做两件事：
  1. 用 fault_mode 选择「可切换故障」，故障只作用于本包自己的配置/节点，
     不改 ROBOTIS 的原始模型文件；
  2. 用 mode 选择「在线仿真」或「离线回放」——回放时不启动 Gazebo，
     也不启动自编 tf 广播器，图像与 /tf 全部由 rosbag 提供，
     这样同一份数据包可以分别跑正常配置和故障配置做对照。

故障定义（两种，都写在 Launch 里，可复现）：
  fault_mode:=topic  话题故障：把图像监测节点的相对话题 image 重映射到
                     /camera/image_missing（不存在、无人发布）。
                     预期：帧率恒为 0，监测节点告警「没有收到图像」，
                     rqt Node Graph 上出现一个没有任何发布者的节点/话题。
  fault_mode:=frame  坐标故障：把 tf 监听节点的 target_frame 改成
                     moving_target_fault（坐标树里不存在）。
                     预期：距离话题输出 NaN（曲线上断线），
                     监听节点报 LookupException，view_frames 里没有这个 frame。
  fault_mode:=none   正常配置（默认）。

用法：
    # 在线仿真（正常）
    ros2 launch tb3_tools bringup.launch.py
    # 在线仿真 + 两种故障
    ros2 launch tb3_tools bringup.launch.py fault_mode:=topic
    ros2 launch tb3_tools bringup.launch.py fault_mode:=frame
    # 离线分析（先起 launch，再在另一个终端 ros2 bag play bags/integrated --clock）
    ros2 launch tb3_tools bringup.launch.py mode:=offline
    ros2 launch tb3_tools bringup.launch.py mode:=offline fault_mode:=topic
    ros2 launch tb3_tools bringup.launch.py mode:=offline fault_mode:=frame
    # 其它
    ros2 launch tb3_tools bringup.launch.py window_sec:=2.0
    ros2 launch tb3_tools bringup.launch.py start_rqt:=false headless:=true

参数：
    mode        sim | offline      默认 sim
    fault_mode  none | topic | frame  默认 none
    window_sec  图像监测统计窗口（秒）  默认 5.0
    start_rqt   是否随 Launch 启动 rqt_plot + rqt_graph  默认 true
    headless    是否不启动 RViz      默认 false
    rviz_config / params_file / x_pose / y_pose 同 integrated.launch.py
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.actions import OpaqueFunction
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

os.environ.setdefault('TURTLEBOT3_MODEL', 'waffle_pi')

# 正常值（来自本工程在 Jazzy 上的实测话题 / frame 名）
NORMAL_IMAGE_TOPIC = '/camera/image_raw'
NORMAL_TARGET_FRAME = 'moving_target'
# 故障注入值：都不存在于本工程运行时的计算图 / 坐标树里
FAULT_IMAGE_TOPIC = '/camera/image_missing'
FAULT_TARGET_FRAME = 'moving_target_fault'


def _as_bool(text):
    return str(text).strip().lower() in ('1', 'true', 'yes', 'on')


def launch_setup(context, *args, **kwargs):
    pkg_share = get_package_share_directory('tb3_tools')

    def get(name):
        return LaunchConfiguration(name).perform(context)

    mode = get('mode').strip().lower()
    fault = get('fault_mode').strip().lower()
    window_sec = get('window_sec')
    start_rqt = _as_bool(get('start_rqt'))
    headless = _as_bool(get('headless'))

    if mode not in ('sim', 'offline'):
        raise RuntimeError(f'mode 只能是 sim 或 offline，收到：{mode}')
    if fault not in ('none', 'topic', 'frame'):
        raise RuntimeError(f'fault_mode 只能是 none / topic / frame，收到：{fault}')

    sim = (mode == 'sim')
    enable_tf = (mode == 'sim')      # 离线回放不能再起自编广播器，否则与 bag 的 /tf 打架
    image_topic = FAULT_IMAGE_TOPIC if fault == 'topic' else NORMAL_IMAGE_TOPIC
    target_frame = FAULT_TARGET_FRAME if fault == 'frame' else NORMAL_TARGET_FRAME

    fault_text = {
        'none': '无故障（正常配置）',
        'topic': (f'话题故障：监测节点重映射到 {FAULT_IMAGE_TOPIC}（无人发布）；'
                  '预期帧率恒为 0 且有「没有收到图像」告警'),
        'frame': (f'坐标故障：监听节点查询 {FAULT_TARGET_FRAME}（树里不存在）；'
                  '预期 LookupException + 距离话题发布 NaN'),
    }[fault]

    actions = [LogInfo(msg=(
        f'[tb3_tools] bringup：mode={mode}，fault_mode={fault}，'
        f'sim={sim}，enable_tf={enable_tf}，window_sec={window_sec}，'
        f'image_topic={image_topic}，target_frame={target_frame}')),
        LogInfo(msg=f'[tb3_tools] 当前配置：{fault_text}')]

    if not sim:
        actions.append(LogInfo(msg=(
            '[tb3_tools] 离线模式：不启动 Gazebo，也不启动自编 tf 广播器；'
            '请在另一个终端执行 ros2 bag play <bag> --clock 提供图像与 /tf')))

    # --- 复用进阶版顶层 Launch，把上面解析好的值传下去 ---------------------
    actions.append(IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(pkg_share, 'launch', 'integrated.launch.py')),
        launch_arguments={
            'sim': str(sim).lower(),
            'enable_tf': str(enable_tf).lower(),
            'use_sim_time': 'true',
            'window_sec': window_sec,
            'image_topic': image_topic,
            'target_frame': target_frame,
            'headless': str(headless).lower(),
            'rviz_config': get('rviz_config'),
            'params_file': get('params_file'),
            'x_pose': get('x_pose'),
            'y_pose': get('y_pose'),
        }.items(),
    ))

    # --- rqt：帧率与距离画在同一张图上，另一窗口看节点连接 -----------------
    if start_rqt:
        actions.append(Node(
            package='rqt_plot',
            executable='rqt_plot',
            name='rqt_plot',
            # rqt_plot 要写到字段级：Float64 话题的数值字段是 data
            arguments=['/image_monitor/fps/data', '/tf_listener/distance/data'],
            output='screen',
        ))
        actions.append(Node(
            package='rqt_graph',
            executable='rqt_graph',
            name='rqt_graph',
            output='screen',
        ))

    return actions


def generate_launch_description():
    pkg_share = get_package_share_directory('tb3_tools')

    return LaunchDescription([
        DeclareLaunchArgument(
            'mode', default_value='sim',
            description='sim=包含 Gazebo 仿真；offline=只用 rosbag 提供输入'),
        DeclareLaunchArgument(
            'fault_mode', default_value='none',
            description='none=正常；topic=图像话题故障；frame=坐标 frame 故障'),
        DeclareLaunchArgument(
            'window_sec', default_value='5.0',
            description='图像监测统计窗口（秒）'),
        DeclareLaunchArgument(
            'start_rqt', default_value='true',
            description='是否随 Launch 启动 rqt_plot 与 rqt_graph'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='true 时不启动 RViz'),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=os.path.join(pkg_share, 'rviz', 'integrated.rviz'),
            description='RViz 配置文件'),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(pkg_share, 'config', 'params.yaml'),
            description='节点参数默认值文件'),
        DeclareLaunchArgument(
            'x_pose', default_value='-2.0', description='小车初始 x 坐标'),
        DeclareLaunchArgument(
            'y_pose', default_value='-0.5', description='小车初始 y 坐标'),
        OpaqueFunction(function=launch_setup),
    ])

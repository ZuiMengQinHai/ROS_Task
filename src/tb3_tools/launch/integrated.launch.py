#!/usr/bin/env python3
"""进阶版顶层 Launch：仿真 + 图像监测 + 自编 tf（静态 / 动态 / 监听）+ RViz。

对应任务书 进阶版 任务 1：
  * 用 IncludeLaunchDescription 包含现成的 turtlebot3_world.launch.py
  * 增加自己的图像监测节点与 RViz 节点
  * 用 Launch 参数 window_sec 控制图像监测的统计窗口
  * 在 Launch 里做话题重映射：把监测节点的相对话题 image 重映射到 image_topic
    （默认 /camera/image_raw），这样节点源码里不出现具体相机话题名
  * 不写死个人路径：rviz / config 一律用 get_package_share_directory 解析

用法：
    ros2 launch tb3_tools integrated.launch.py
    ros2 launch tb3_tools integrated.launch.py window_sec:=2.0          # 改统计窗口
    ros2 launch tb3_tools integrated.launch.py image_topic:=/scan       # 改重映射（错误示范）
    ros2 launch tb3_tools integrated.launch.py headless:=true           # 不弹 RViz
    ros2 launch tb3_tools integrated.launch.py sim:=false enable_tf:=false
        # ↑ 离线模式：不启动 Gazebo，也不启动自编 tf 广播器，
        #   由 rosbag 提供图像与 tf（挑战版的离线分析就用这条）

参数一览（ros2 launch ... --show-args 可查）：
    use_sim_time  sim  enable_tf  window_sec  image_topic  target_frame
    rviz_config   params_file  headless  x_pose  y_pose
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

# 上游 spawn 启动文件在解析期就读取 TURTLEBOT3_MODEL，缺失会 KeyError
os.environ.setdefault('TURTLEBOT3_MODEL', 'waffle_pi')


def _as_bool(text):
    return str(text).strip().lower() in ('1', 'true', 'yes', 'on')


def launch_setup(context, *args, **kwargs):
    """在 Launch 参数已求值后组装节点，需要的值都转成 Python 原生类型。"""
    pkg_share = get_package_share_directory('tb3_tools')
    tb3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')

    def get(name):
        return LaunchConfiguration(name).perform(context)

    use_sim_time = _as_bool(get('use_sim_time'))
    sim = _as_bool(get('sim'))
    enable_tf = _as_bool(get('enable_tf'))
    headless = _as_bool(get('headless'))
    window_sec = float(get('window_sec'))
    image_topic = get('image_topic')
    target_frame = get('target_frame')
    rviz_config = get('rviz_config')
    params_file = get('params_file')
    x_pose = get('x_pose')
    y_pose = get('y_pose')

    actions = [LogInfo(msg=(
        f'[tb3_tools] 进阶版顶层 Launch 已启动：TURTLEBOT3_MODEL='
        f'{os.environ.get("TURTLEBOT3_MODEL", "(未设置)")}，'
        f'use_sim_time={use_sim_time}，sim={sim}，enable_tf={enable_tf}，'
        f'window_sec={window_sec:.1f}，image_topic={image_topic}，'
        f'target_frame={target_frame}'))]

    # --- 1. 包含现成仿真启动文件 -------------------------------------------
    if sim:
        actions.append(IncludeLaunchDescription(
            PythonLaunchDescriptionSource(
                os.path.join(tb3_gazebo_share, 'launch',
                             'turtlebot3_world.launch.py')),
            launch_arguments={
                'use_sim_time': str(use_sim_time).lower(),
                'x_pose': x_pose,
                'y_pose': y_pose,
            }.items(),
        ))

    # --- 2. 图像监测节点（参数 + 重映射）-----------------------------------
    # 节点源码订阅相对话题名 image；这里 remap 成 image_topic；
    # Launch 参数 window_sec 通过 parameters 字典覆盖节点默认值。
    actions.append(Node(
        package='tb3_tools',
        executable='image_monitor',
        name='image_monitor',
        parameters=[params_file, {
            'use_sim_time': use_sim_time,
            'window_sec': window_sec,
        }],
        remappings=[('image', image_topic)],
        output='screen',
    ))

    # --- 3. 自编 tf：静态广播（base_link → inspection_point）---------------
    # 回放时必须关掉（enable_tf:=false），否则会和 bag 里的 /tf 打架
    #
    # 关于参数覆盖（实测踩坑）：Node(parameters=[yaml 路径, {字典}]) 里的字典会被
    # launch_ros 写成「通配符段落 /**」的临时参数文件；如果 params.yaml 里还有
    # 同名参数写在「按节点名」的段落（image_monitor: / tf_listener:）下，
    # 按节点名的优先级更高，覆盖就不生效（现象：window_sec 一直是 5.0、
    # target_frame 注入不进去）。因此本工程把 window_sec 与 target_frame
    # 从 params.yaml 的节点段落里**删掉**，只留在节点代码默认值 + Launch 里，
    # 这样通配符段落就是唯一来源，覆盖必然生效。
    if enable_tf:
        actions.append(Node(
            package='tb3_tools',
            executable='static_tf_broadcaster',
            name='static_tf_broadcaster',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            output='screen',
        ))
        actions.append(Node(
            package='tb3_tools',
            executable='dynamic_tf_broadcaster',
            name='dynamic_tf_broadcaster',
            parameters=[params_file, {'use_sim_time': use_sim_time}],
            output='screen',
        ))

    # --- 4. 自编 tf：监听节点（距离）---------------------------------------
    actions.append(Node(
        package='tb3_tools',
        executable='tf_listener',
        name='tf_listener',
        parameters=[params_file, {
            'use_sim_time': use_sim_time,
            'target_frame': target_frame,
        }],
        output='screen',
    ))

    # --- 5. RViz -----------------------------------------------------------
    if not headless:
        actions.append(Node(
            package='rviz2',
            executable='rviz2',
            name='rviz2',
            arguments=['-d', rviz_config],
            parameters=[{'use_sim_time': use_sim_time}],
            output='screen',
        ))

    return actions


def generate_launch_description():
    pkg_share = get_package_share_directory('tb3_tools')

    return LaunchDescription([
        DeclareLaunchArgument(
            'sim', default_value='true',
            description='是否包含 Gazebo 仿真；离线回放时设 false'),
        DeclareLaunchArgument(
            'enable_tf', default_value='true',
            description='是否启动自编静态/动态 tf 广播器；离线回放时必须 false'),
        DeclareLaunchArgument(
            'use_sim_time', default_value='true',
            description='使用 /clock 仿真时间（仿真与 bag 回放都必须 true）'),
        DeclareLaunchArgument(
            'window_sec', default_value='5.0',
            description='图像监测的统计窗口长度（秒）'),
        DeclareLaunchArgument(
            'image_topic', default_value='/camera/image_raw',
            description='监测节点重映射后的实际图像话题'),
        DeclareLaunchArgument(
            'target_frame', default_value='moving_target',
            description='tf 监听要查询的目标坐标系'),
        DeclareLaunchArgument(
            'rviz_config',
            default_value=os.path.join(pkg_share, 'rviz', 'integrated.rviz'),
            description='RViz 配置文件（本包 install 目录下的 integrated.rviz）'),
        DeclareLaunchArgument(
            'params_file',
            default_value=os.path.join(pkg_share, 'config', 'params.yaml'),
            description='各节点参数默认值文件'),
        DeclareLaunchArgument(
            'headless', default_value='false',
            description='true 时不启动 RViz'),
        DeclareLaunchArgument(
            'x_pose', default_value='-2.0', description='小车初始 x 坐标'),
        DeclareLaunchArgument(
            'y_pose', default_value='-0.5', description='小车初始 y 坐标'),
        OpaqueFunction(function=launch_setup),
    ])

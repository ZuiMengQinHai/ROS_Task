#!/usr/bin/env python3
"""基础版顶层 Launch：一条命令拉起「Gazebo 仿真 + RViz 观察」。

对应任务书 基础版 任务 1：
  * 包含现成的 turtlebot3_gazebo/turtlebot3_world.launch.py（不改上游模型文件）
  * 启动 RViz，加载本包自己的 rviz/basic.rviz
  * 全局设置 use_sim_time:=true
  * 不写死个人电脑的绝对路径 —— 一律用 get_package_share_directory 解析

用法：
    ros2 launch tb3_tools basic.launch.py
    ros2 launch tb3_tools basic.launch.py rviz_config:=/path/to/other.rviz
    ros2 launch tb3_tools basic.launch.py headless:=true    # 只起 Gazebo，不弹 RViz
"""

import os

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch.actions import DeclareLaunchArgument
from launch.actions import IncludeLaunchDescription
from launch.actions import LogInfo
from launch.conditions import UnlessCondition
from launch.launch_description_sources import PythonLaunchDescriptionSource
from launch.substitutions import LaunchConfiguration
from launch_ros.actions import Node

# ---------------------------------------------------------------------------
# 上游 turtlebot3_gazebo/launch/spawn_turtlebot3.launch.py 在**文件解析期**就执行
#     TURTLEBOT3_MODEL = os.environ['TURTLEBOT3_MODEL']
# 变量缺失会直接 KeyError。这里在模块导入期兜底设成任务书指定的 waffle_pi，
# 这样即使用户忘了 export，本 Launch 也能独立跑起来。
# 用 setdefault：如果用户已经在 shell 里 export 了别的值，以用户为准。
# ---------------------------------------------------------------------------
os.environ.setdefault('TURTLEBOT3_MODEL', 'waffle_pi')


def generate_launch_description():
    pkg_share = get_package_share_directory('tb3_tools')
    turtlebot3_gazebo_share = get_package_share_directory('turtlebot3_gazebo')

    # --- Launch 参数 ---------------------------------------------------------
    use_sim_time = LaunchConfiguration('use_sim_time')
    rviz_config = LaunchConfiguration('rviz_config')
    headless = LaunchConfiguration('headless')
    x_pose = LaunchConfiguration('x_pose')
    y_pose = LaunchConfiguration('y_pose')

    declare_use_sim_time = DeclareLaunchArgument(
        'use_sim_time', default_value='true',
        description='是否使用 Gazebo 的仿真时间。必须为 true，'
                    '否则 RViz 的 TF/LaserScan/Image 会因时间戳对不上而显示不出来')

    declare_rviz_config = DeclareLaunchArgument(
        'rviz_config',
        default_value=os.path.join(pkg_share, 'rviz', 'basic.rviz'),
        description='RViz 配置文件。默认使用本功能包 install 目录下的 basic.rviz')

    declare_headless = DeclareLaunchArgument(
        'headless', default_value='false',
        description='true 时只启动仿真，不启动 RViz')

    declare_x_pose = DeclareLaunchArgument(
        'x_pose', default_value='-2.0', description='小车初始 x 坐标（世界坐标系）')
    declare_y_pose = DeclareLaunchArgument(
        'y_pose', default_value='-0.5', description='小车初始 y 坐标（世界坐标系）')

    # --- 包含现成的仿真启动文件 ---------------------------------------------
    # 上游会拉起：gz server（-r -s）、gz client（-g）、
    #             robot_state_publisher、spawn 小车、ros_gz 桥接、图像桥接
    turtlebot3_world = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(turtlebot3_gazebo_share, 'launch',
                         'turtlebot3_world.launch.py')
        ),
        launch_arguments={
            'use_sim_time': use_sim_time,
            'x_pose': x_pose,
            'y_pose': y_pose,
        }.items(),
    )

    # --- RViz ---------------------------------------------------------------
    rviz = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2',
        arguments=['-d', rviz_config],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen',
        condition=UnlessCondition(headless),
    )

    info = LogInfo(
        msg=['[tb3_tools] 顶层 Launch 已启动：'
             'TURTLEBOT3_MODEL=', os.environ.get('TURTLEBOT3_MODEL', '(未设置)'),
             '，仿真时间 use_sim_time=', use_sim_time])

    return LaunchDescription([
        declare_use_sim_time,
        declare_rviz_config,
        declare_headless,
        declare_x_pose,
        declare_y_pose,
        info,
        turtlebot3_world,
        rviz,
    ])

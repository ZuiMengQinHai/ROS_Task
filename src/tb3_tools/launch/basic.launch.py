"""基础版顶层 Launch —— 【基础版 任务 1】骨架，尚未实现。

要求（来自任务书）：
  1. IncludeLaunchDescription 包含现成的
     turtlebot3_gazebo/turtlebot3_world.launch.py（不要自己写 URDF/SDF/xacro）
  2. 启动 RViz（rviz2），加载本包的 rviz/basic.rviz
  3. 全局设置 use_sim_time:=true
  4. 不写死绝对路径 —— 用 ament_index_python.packages.get_package_share_directory

参考写法（实现时启用）：

    from ament_index_python.packages import get_package_share_directory
    from launch import LaunchDescription
    from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument
    from launch.launch_description_sources import PythonLaunchDescriptionSource
    from launch.substitutions import LaunchConfiguration
    from launch_ros.actions import Node

    sim = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(
            os.path.join(get_package_share_directory('turtlebot3_gazebo'),
                         'launch', 'turtlebot3_world.launch.py')))
"""


def generate_launch_description():
    raise NotImplementedError('TODO: basic.launch.py 尚未实现（见任务书 基础版 任务 1）')

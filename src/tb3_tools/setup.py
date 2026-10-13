from glob import glob

from setuptools import find_packages, setup

package_name = 'tb3_tools'

setup(
    name=package_name,
    version='0.1.0',
    packages=find_packages(exclude=['test']),
    data_files=[
        ('share/ament_index/resource_index/packages', ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
        # 不写死绝对路径：这些相对路径在编译时被解析成 install/share 下的实际位置
        ('share/' + package_name + '/launch', glob('launch/*.launch.py')),
        ('share/' + package_name + '/rviz', glob('rviz/*.rviz')),
        ('share/' + package_name + '/config', glob('config/*.yaml')),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='ubuntu',
    maintainer_email='ubuntu@ubuntu-ros2.local',
    description='TurtleBot3 Waffle Pi simulation toolchain for the Chapter 3 project',
    license='Apache-2.0',
    entry_points={
        'console_scripts': [
            # 进阶版：图像帧率监测节点（订阅相机图像，发布可供 rqt Plot 绘图的数值话题）
            'image_monitor = tb3_tools.image_monitor:main',
            # 进阶版：静态 tf 广播器（base_link -> inspection_point）
            'static_tf_broadcaster = tb3_tools.static_tf_broadcaster:main',
            # 进阶版：动态 tf 广播器（odom -> moving_target）
            'dynamic_tf_broadcaster = tb3_tools.dynamic_tf_broadcaster:main',
            # 进阶版：tf 监听节点（查询 base_link -> moving_target 并输出距离）
            'tf_listener = tb3_tools.tf_listener:main',
        ],
    },
)

#!/usr/bin/env python3
"""动态 tf 广播器 —— 【进阶版 任务 3】。

用 tf2_ros.TransformBroadcaster 在 odom 下新增 moving_target
（父 odom，子 moving_target），让该目标按自定周期做圆周运动：
一个运动周期里角度从 0 走满 2π，位置
    x = radius_m * cos(θ)，y = radius_m * sin(θ)，z = z_m
姿态取切线方向（yaw = θ + π/2），这样 RViz 里的坐标轴能看出它在「绕着走」。

时间基：节点时钟。仿真运行时即 Gazebo 的 /clock（use_sim_time=true），
bag 回放时同样由 bag 的 /clock 驱动 —— 本节点在回放场景下不启动，
moving_target 由 bag 里的 /tf 提供。

不重复广播已有关系：本节点只发 odom → moving_target，
不碰 odom → base_footprint（那是 ros_gz_bridge 的职责）。

参数：parent_frame, child_frame, period_sec, radius_m, z_m, publish_rate_hz
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros import TransformBroadcaster


class DynamicTfBroadcaster(Node):
    """按周期沿圆周运动地发布 odom → moving_target。"""

    def __init__(self):
        super().__init__('dynamic_tf_broadcaster')

        self.declare_parameter('parent_frame', 'odom')
        self.declare_parameter('child_frame', 'moving_target')
        self.declare_parameter('period_sec', 8.0)
        self.declare_parameter('radius_m', 1.2)
        self.declare_parameter('z_m', 0.3)
        self.declare_parameter('publish_rate_hz', 20.0)

        self._parent = str(self.get_parameter('parent_frame').value)
        self._child = str(self.get_parameter('child_frame').value)
        self._period = max(1.0, float(self.get_parameter('period_sec').value))
        self._radius = float(self.get_parameter('radius_m').value)
        self._z = float(self.get_parameter('z_m').value)
        rate = max(1.0, float(self.get_parameter('publish_rate_hz').value))

        self._broadcaster = TransformBroadcaster(self)
        self._timer = self.create_timer(1.0 / rate, self._on_timer)
        self._last_logged = None

        self.get_logger().info(
            f'动态 tf 广播器启动：{self._parent} → {self._child}，'
            f'周期 {self._period:.1f}s，半径 {self._radius:.2f}m，'
            f'发布频率 {rate:.1f}Hz（时间基 = 节点时钟 / /clock）')

    def _on_timer(self):
        now = self.get_clock().now()
        t = now.nanoseconds * 1e-9
        theta = 2.0 * math.pi * (t / self._period)

        t_msg = TransformStamped()
        t_msg.header.stamp = now.to_msg()
        t_msg.header.frame_id = self._parent
        t_msg.child_frame_id = self._child

        t_msg.transform.translation.x = self._radius * math.cos(theta)
        t_msg.transform.translation.y = self._radius * math.sin(theta)
        t_msg.transform.translation.z = self._z

        # 姿态：切线方向（绕 z 轴），半角公式直接写四元数
        half = (theta + math.pi * 0.5) * 0.5
        t_msg.transform.rotation.x = 0.0
        t_msg.transform.rotation.y = 0.0
        t_msg.transform.rotation.z = math.sin(half)
        t_msg.transform.rotation.w = math.cos(half)

        self._broadcaster.sendTransform(t_msg)

        # 每运动周期打一行：位置随仿真时间在圆周上推进，便于事后核对
        marker = int(t / self._period)
        if marker != self._last_logged:
            self._last_logged = marker
            self.get_logger().info(
                f'{self._child} 位置（{self._parent} 系）：'
                f'x={t_msg.transform.translation.x:+.2f} '
                f'y={t_msg.transform.translation.y:+.2f} '
                f'z={self._z:+.2f}，仿真时刻 {t:.1f}s')


def main(args=None):
    rclpy.init(args=args)
    node = DynamicTfBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('收到 Ctrl+C，dynamic_tf_broadcaster 退出')
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001
            pass


if __name__ == '__main__':
    main()

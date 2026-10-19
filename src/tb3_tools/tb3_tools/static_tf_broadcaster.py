#!/usr/bin/env python3
"""静态 tf 广播器 —— 【进阶版 任务 3】。

用 tf2_ros.StaticTransformBroadcaster 在现有 base_link 下新增 inspection_point
（父 base_link，子 inspection_point），表示车体上一个**机械上固定不变**的检查点。

为什么用静态广播：这条变换与时间无关，只需要发一次，走 /tf_static
（transient_local QoS）——晚加入的订阅者（RViz、tf2_echo）也能拿到历史值，
不必按固定频率重复发送，省带宽也不会让 TF 缓存重复数据告警。

不冲突检查（与本模型已有 frame）：base_footprint / base_link /
camera_link / camera_rgb_frame / imu_link / wheel_* 均未被占用，
也不广播已有关系 odom → base_footprint。

参数：parent_frame, child_frame, x, y, z, roll, pitch, yaw
"""

import math

import rclpy
from rclpy.node import Node
from geometry_msgs.msg import TransformStamped
from tf2_ros.static_transform_broadcaster import StaticTransformBroadcaster


def quaternion_from_euler(roll, pitch, yaw):
    """(roll, pitch, yaw) → 四元数 (x, y, z, w)，ZYX 顺序（ROS 约定）。"""
    cr, sr = math.cos(roll * 0.5), math.sin(roll * 0.5)
    cp, sp = math.cos(pitch * 0.5), math.sin(pitch * 0.5)
    cy, sy = math.cos(yaw * 0.5), math.sin(yaw * 0.5)
    return (
        sr * cp * cy - cr * sp * sy,
        cr * sp * cy + sr * cp * sy,
        cr * cp * sy - sr * sp * cy,
        cr * cp * cy + sr * sp * sy,
    )


class StaticTfBroadcaster(Node):
    """发布 base_link → inspection_point（默认值）的静态变换。"""

    def __init__(self):
        super().__init__('static_tf_broadcaster')

        self.declare_parameter('parent_frame', 'base_link')
        self.declare_parameter('child_frame', 'inspection_point')
        self.declare_parameter('x', 0.15)
        self.declare_parameter('y', 0.0)
        self.declare_parameter('z', 0.20)
        self.declare_parameter('roll', 0.0)
        self.declare_parameter('pitch', 0.0)
        self.declare_parameter('yaw', 0.0)

        parent = str(self.get_parameter('parent_frame').value)
        child = str(self.get_parameter('child_frame').value)
        xyz = (float(self.get_parameter('x').value),
               float(self.get_parameter('y').value),
               float(self.get_parameter('z').value))
        rpy = (float(self.get_parameter('roll').value),
               float(self.get_parameter('pitch').value),
               float(self.get_parameter('yaw').value))

        self._broadcaster = StaticTransformBroadcaster(self)

        t = TransformStamped()
        t.header.stamp = self.get_clock().now().to_msg()
        t.header.frame_id = parent
        t.child_frame_id = child
        t.transform.translation.x = xyz[0]
        t.transform.translation.y = xyz[1]
        t.transform.translation.z = xyz[2]
        qx, qy, qz, qw = quaternion_from_euler(*rpy)
        t.transform.rotation.x = qx
        t.transform.rotation.y = qy
        t.transform.rotation.z = qz
        t.transform.rotation.w = qw

        self._broadcaster.sendTransform(t)
        self.get_logger().info(
            f'静态 tf 已发布（/tf_static，transient_local）：{parent} → {child}，'
            f'平移 [{xyz[0]:.3f}, {xyz[1]:.3f}, {xyz[2]:.3f}]，'
            f'rpy [{rpy[0]:.3f}, {rpy[1]:.3f}, {rpy[2]:.3f}]')
        self.get_logger().info(
            '静态变换只需发一次；节点保持运行即可，晚启动的 RViz / tf2_echo '
            '仍能通过 transient_local 拿到这条变换')


def main(args=None):
    rclpy.init(args=args)
    node = StaticTfBroadcaster()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('收到 Ctrl+C，static_tf_broadcaster 退出')
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001
            pass


if __name__ == '__main__':
    main()

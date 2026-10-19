#!/usr/bin/env python3
"""图像帧率监测节点 —— 【进阶版 任务 2】。

订阅相机图像，在**可配置的时间窗口**内统计接收帧率，并把帧率发布成一个
数值话题，供 rqt Plot 画曲线。只统计消息数量，不解析图像内容。

话题约定：
  输入：相对名 ``image``（由 Launch 通过 remap 注入 /camera/image_raw；
        也可用 ``-r image:=/camera/image_raw`` 手动指定）
  输出：``fps``（节点名 image_monitor → 默认 /image_monitor/fps）
        类型 std_msgs/msg/Float64

参数：
  window_sec          统计窗口长度（秒），Launch 参数 window_sec 可覆盖
  publish_period_sec  数值话题发布周期（秒）
  fps_topic           输出话题名
  stale_warn_sec      超过这么久没收到图像就打一条告警（用于定位话题故障）

帧率口径：用**图像消息头里的仿真时间戳**计算窗口内 (帧数-1)/时间跨度，
得到「每个仿真秒收到多少帧」，与仿真实时快慢无关；同一段 bag 回放时
结论可复现。
"""

import collections
import time

import rclpy
from rclpy.node import Node
from rclpy.qos import qos_profile_sensor_data
from sensor_msgs.msg import Image
from std_msgs.msg import Float64


class ImageMonitor(Node):
    """统计图像帧率并发布数值话题。"""

    def __init__(self):
        super().__init__('image_monitor')

        self.declare_parameter('window_sec', 5.0)
        self.declare_parameter('publish_period_sec', 1.0)
        # 私有名 ~/fps：节点名 image_monitor 时解析为 /image_monitor/fps
        self.declare_parameter('fps_topic', '~/fps')
        self.declare_parameter('stale_warn_sec', 3.0)

        self._window_sec = max(0.5, float(self.get_parameter('window_sec').value))
        period = max(0.1, float(self.get_parameter('publish_period_sec').value))
        self._stale_warn_sec = max(1.0, float(
            self.get_parameter('stale_warn_sec').value))
        fps_topic = str(self.get_parameter('fps_topic').value)

        self._stamps = collections.deque()   # 窗口内图像消息的 sim 时间戳
        self._total = 0                      # 累计收到的帧数
        self._last_stamp = None              # 上一帧的时间戳
        self._last_rx_wall = None            # 上一帧的墙钟时刻（判断「没数据」）
        self._last_stale_warn = None
        self._ticks = 0

        # 图像是大消息，用 SensorData QoS（Best Effort）订阅：
        # 既能配 Reliable 的 ros_gz_bridge，也能配 Best Effort 的其它图像源
        self._sub = self.create_subscription(
            Image, 'image', self._on_image, qos_profile_sensor_data)
        self._pub = self.create_publisher(Float64, fps_topic, 10)
        self._timer = self.create_timer(period, self._on_timer)

        self.get_logger().info(
            f'image_monitor 启动：统计窗口 window_sec={self._window_sec:.1f}s，'
            f'发布周期 {period:.1f}s，输出话题 {self._pub.topic_name}'
            '（std_msgs/Float64）')
        self.get_logger().info(
            '输入是相对话题名 image，由 Launch remap 决定实际话题；'
            '可用 ros2 topic info 或 rqt Node Graph 确认')

    # ------------------------------------------------------------------ 回调
    def _on_image(self, msg):
        stamp = msg.header.stamp
        t = stamp.sec + stamp.nanosec * 1e-9
        if t <= 0.0:
            # 个别图像源不填时间戳时退回节点时钟（本工程为仿真时间）
            t = self.get_clock().now().nanoseconds * 1e-9

        if self._last_stamp is not None and t < self._last_stamp - 1e-6:
            # 时间戳回退（例如 bag 循环回放）时清空窗口，避免算出负帧率
            self._stamps.clear()

        self._stamps.append(t)
        self._last_stamp = t
        self._last_rx_wall = time.monotonic()
        self._total += 1

    def _on_timer(self):
        now_wall = time.monotonic()
        newest = self._stamps[-1] if self._stamps else None

        # 只保留窗口内的帧
        if newest is not None:
            while self._stamps and newest - self._stamps[0] > self._window_sec:
                self._stamps.popleft()

        stale = (self._last_rx_wall is None
                 or (now_wall - self._last_rx_wall) > self._stale_warn_sec)
        if stale:
            self._stamps.clear()

        fps = 0.0
        if len(self._stamps) >= 2:
            span = self._stamps[-1] - self._stamps[0]
            if span > 1e-6:
                fps = (len(self._stamps) - 1) / span

        self._pub.publish(Float64(data=float(fps)))

        if stale:
            if (self._last_stale_warn is None
                    or now_wall - self._last_stale_warn > self._stale_warn_sec):
                self._last_stale_warn = now_wall
                self.get_logger().warning(
                    f'已 {self._stale_warn_sec:.1f}s 以上没有收到图像消息，帧率按 0 发布。'
                    '排查顺序：ros2 topic list -t 看图像话题是否存在 → '
                    'ros2 topic hz <话题> 看有没有数据 → '
                    'rqt Node Graph 看 remap 后的连接是否落到别的话题')
            return

        self._last_stale_warn = None
        self._ticks += 1
        # 每 5 次发布（默认 5s）打印一行：既能核对数值，又不刷屏
        if self._ticks % 5 == 0:
            self.get_logger().info(
                f'窗口 {self._window_sec:.1f}s 内 {len(self._stamps)} 帧 → '
                f'{fps:.2f} fps（累计 {self._total} 帧）')


def main(args=None):
    rclpy.init(args=args)
    node = ImageMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('收到 Ctrl+C，image_monitor 退出')
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001 - 已关闭时忽略
            pass


if __name__ == '__main__':
    main()

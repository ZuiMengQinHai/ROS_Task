#!/usr/bin/env python3
"""tf 监听节点 —— 【进阶版 任务 4】。

用 tf2_ros.Buffer + tf2_ros.TransformListener 查询 base_link → moving_target
的相对变换，输出两者距离，并发布数值话题供 rqt Plot 与帧率曲线一起对照。

异常处理（任务书明确要求）：
  * LookupException        —— 坐标系尚不存在（例如目标 frame 写错、广播器未启动）
  * ConnectivityException  —— 两 frame 之间链路不连通（坐标树断链）
  * ExtrapolationException —— 时间戳暂时不匹配（如刚启动、时间跳变）
  以上都属于 tf2_ros.TransformException。出错时：
    - 发布 NaN（rqt Plot 上表现为曲线断开，而不是画一条假的 0）
    - 打印带排查建议的告警（同一错误 2s 内不重复刷屏）
    - 恢复正常时补一条「恢复」日志，便于在 rqt Console 里定位故障区间

参数：source_frame, target_frame, lookup_period_sec, timeout_sec, distance_topic
"""

import math
import time as _time

import rclpy
from rclpy.duration import Duration
from rclpy.node import Node
from rclpy.time import Time
from std_msgs.msg import Float64
import tf2_ros


class TfListener(Node):
    """周期查询 base_link → moving_target 并发布距离。"""

    def __init__(self):
        super().__init__('tf_listener')

        self.declare_parameter('source_frame', 'base_link')
        self.declare_parameter('target_frame', 'moving_target')
        self.declare_parameter('lookup_period_sec', 0.2)
        self.declare_parameter('timeout_sec', 0.2)
        self.declare_parameter('distance_topic', '/tf_listener/distance')
        self.declare_parameter('error_warn_sec', 2.0)

        self._source = str(self.get_parameter('source_frame').value)
        self._target = str(self.get_parameter('target_frame').value)
        period = max(0.05, float(self.get_parameter('lookup_period_sec').value))
        self._timeout = float(self.get_parameter('timeout_sec').value)
        self._warn_interval = max(0.5, float(
            self.get_parameter('error_warn_sec').value))
        distance_topic = str(self.get_parameter('distance_topic').value)

        self._buffer = tf2_ros.Buffer(cache_time=Duration(seconds=10.0))
        self._listener = tf2_ros.TransformListener(self._buffer, self)
        self._pub = self.create_publisher(Float64, distance_topic, 10)
        self._timer = self.create_timer(period, self._on_timer)

        self._last_error_kind = None
        self._last_error_wall = None
        self._ok_count = 0
        self._err_count = 0
        self._last_distance = None

        self.get_logger().info(
            f'tf_listener 启动：查询 {self._target} 在 {self._source} 中的位置，'
            f'查询周期 {period:.2f}s，超时 {self._timeout:.2f}s，'
            f'距离发布到 {distance_topic}（std_msgs/Float64）')

    # ------------------------------------------------------------------ 定时查询
    def _on_timer(self):
        stamp = Time()  # 取最新可用时刻（仿真时间下即 /clock 当前时刻）
        try:
            tr = self._buffer.lookup_transform(
                self._target, self._source, stamp,
                timeout=Duration(seconds=self._timeout))
        except tf2_ros.LookupException as exc:
            self._fail('LookupException', exc,
                       f'坐标系不存在或尚无数据：{self._target} / {self._source}；'
                       '用 ros2 run tf2_tools view_frames 看树里有没有该 frame，'
                       '用 ros2 run tf2_ros tf2_echo 单独确认')
            return
        except tf2_ros.ConnectivityException as exc:
            self._fail('ConnectivityException', exc,
                       '两个 frame 之间坐标树不连通；'
                       'view_frames 里检查是否有断开的子树')
            return
        except tf2_ros.ExtrapolationException as exc:
            self._fail('ExtrapolationException', exc,
                       '时间戳暂时对不上（刚启动或时间跳变）；'
                       '通常是启动瞬态，持续出现则检查各广播器是否用同一时间基')
            return
        except tf2_ros.TransformException as exc:  # 兜底：其它 tf2 异常
            self._fail('TransformException', exc, '未分类的 tf2 异常')
            return

        t = tr.transform.translation
        distance = math.sqrt(t.x * t.x + t.y * t.y + t.z * t.z)
        self._pub.publish(Float64(data=float(distance)))

        self._ok_count += 1
        if self._err_count:
            self.get_logger().info(
                f'查询恢复正常（此前连续错误 {self._err_count} 次），'
                f'当前距离 {distance:.3f} m')
            self._err_count = 0
            self._last_error_kind = None

        # 每 25 次（默认 5s）打印一次当前位置与距离
        if self._ok_count % 25 == 0:
            self.get_logger().info(
                f'{self._target} 相对 {self._source}：'
                f'x={t.x:+.3f} y={t.y:+.3f} z={t.z:+.3f} → 距离 {distance:.3f} m')

    def _fail(self, kind, exc, hint):
        now_wall = _time.monotonic()
        self._err_count += 1
        self._pub.publish(Float64(data=float('nan')))

        if (self._last_error_kind != kind
                or self._last_error_wall is None
                or now_wall - self._last_error_wall > self._warn_interval):
            self._last_error_kind = kind
            self._last_error_wall = now_wall
            self.get_logger().warning(
                f'tf 查询失败 [{kind}]：{exc}\n  处理建议：{hint}')


def main(args=None):
    rclpy.init(args=args)
    node = TfListener()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info('收到 Ctrl+C，tf_listener 退出')
    finally:
        node.destroy_node()
        try:
            rclpy.shutdown()
        except Exception:  # noqa: BLE001
            pass


if __name__ == '__main__':
    main()

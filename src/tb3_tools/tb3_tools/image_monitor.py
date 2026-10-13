#!/usr/bin/env python3
"""图像监测节点 —— 【进阶版 任务 2】骨架，尚未实现。

设计要点（待实现）：
  * 订阅相机图像（话题由 launch 通过重映射注入，默认 /camera/image_raw）
  * 在可配置的时间窗口内统计接收帧率
  * 发布一个 std_msgs/msg/Float32 数值话题，供 rqt Plot 绘图
    —— 话题名待定，建议 /image_monitor/fps
  * 只统计消息，不做任何图像内容识别
  * 参数：统计窗口长度、输出话题名、发布周期
"""


def main():
    raise SystemExit('TODO: 图像监测节点尚未实现（见任务书 进阶版 任务 2）')


if __name__ == '__main__':
    main()

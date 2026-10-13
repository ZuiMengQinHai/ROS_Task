#!/usr/bin/env python3
"""tf 监听节点 —— 【进阶版 任务 4】骨架，尚未实现。

设计要点（待实现）：
  * 使用 tf2_ros.Buffer + tf2_ros.TransformListener
  * lookup_transform 查询 base_link -> moving_target，输出两者距离
  * 必须处理异常：
      - tf2_ros.LookupException（坐标系尚不存在）
      - tf2_ros.ExtrapolationException（时间戳暂不匹配）
      - tf2_ros.ConnectivityException（链路不连通）
  * 参数：源/目标 frame、查询周期、超时
"""


def main():
    raise SystemExit('TODO: tf 监听节点尚未实现（见任务书 进阶版 任务 4）')


if __name__ == '__main__':
    main()

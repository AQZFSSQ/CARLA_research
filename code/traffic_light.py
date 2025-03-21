import carla
import time

def main():
    # 创建一个客户端并连接到Carla服务器
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    
    # 获取世界
    world = client.get_world()

    # 获取蓝图库
    blueprint_library = world.get_blueprint_library()

    # 选择车辆蓝图
    vehicle_bp = blueprint_library.filter('vehicle.*')[0]

    # 选择起始点
    spawn_points = world.get_map().get_spawn_points()
    spawn_point = spawn_points[0] if spawn_points else None

    # 创建车辆
    vehicle = world.try_spawn_actor(vehicle_bp, spawn_point)

    # 确保车辆成功生成
    if vehicle is None:
        print("Failed to spawn vehicle")
        return

    # 将车辆设置为自动驾驶
    vehicle.set_autopilot(True)

    # 主循环，持续监控交通信号灯
    try:
        while True:
            # 获取车辆前方的交通信号灯
            traffic_light = vehicle.get_traffic_light()

            if traffic_light is not None:
                # 获取信号灯状态
                traffic_light_state = traffic_light.get_state()

                # 根据交通信号灯状态决定车辆行为
                if traffic_light_state == carla.TrafficLightState.Red:
                    print("Red light - Vehicle should stop")
                    vehicle.apply_control(carla.VehicleControl(throttle=0.0, brake=1.0))
                elif traffic_light_state == carla.TrafficLightState.Green:
                    print("Green light - Vehicle can go")
                    vehicle.apply_control(carla.VehicleControl(throttle=0.5, brake=0.0))
                elif traffic_light_state == carla.TrafficLightState.Yellow:
                    print("Yellow light - Vehicle should prepare to stop")
                    vehicle.apply_control(carla.VehicleControl(throttle=0.2, brake=0.3))
            
            # 等待一段时间以免过于频繁地改变控制
            time.sleep(0.1)
    finally:
        # 销毁车辆
        vehicle.destroy()

if __name__ == '__main__':
    main()

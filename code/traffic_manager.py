import carla
import random
import time

def main():
    # 连接到Carla服务器
    client = carla.Client('127.0.0.1', 2000)
    client.set_timeout(10.0)
    
    # 获取当前的模拟世界
    world = client.get_world()
    
    # 获取当前的交通管理器实例
    traffic_manager = client.get_trafficmanager()
    
    # 生成车辆
    blueprint_library = world.get_blueprint_library()
    vehicle_blueprints = blueprint_library.filter('vehicle.*')
    spawn_points = world.get_map().get_spawn_points()
    random.shuffle(spawn_points)  # 随机打乱生成点

    vehicles = []
    for i in range(5):  # 生成5辆车
        blueprint = random.choice(vehicle_blueprints)
        transform = spawn_points[i]
        vehicle = world.spawn_actor(blueprint, transform)
        vehicle.set_autopilot(True)  # 启用自动驾驶
        vehicles.append(vehicle)

    # 设置所有车辆的跟车距离（以米为单位）
    traffic_manager.set_global_distance_to_leading_vehicle(2.5)

    # 设置特定车辆相对于前车的跟车距离
    for vehicle in vehicles:
        traffic_manager.set_distance_to_leading_vehicle(vehicle.id, 2.5)

    # 设置车辆在自动驾驶模式下忽略其他车辆的百分比
    # 例如，设置为50%则车辆会忽略50%的其他车辆
    for vehicle in vehicles:
        traffic_manager.ignore_vehicles_percentage(vehicle.id, 50)

    # 设置特定车辆的最大速度限制（以米每秒为单位）
    for vehicle in vehicles:
        traffic_manager.set_speed_limit(vehicle.id, 15.0)  # 设置最大速度为15米/秒

    # 控制交通参与者的行为，强制特定车辆变道
    if vehicles:
        traffic_manager.force_lane_change(vehicles[0].id)  # 强制第一辆车变道

    # 设置交通信号灯的状态示例
    # 这里假设有一个交通信号灯的ID为1，状态为红灯
    # traffic_manager.set_traffic_light_state(1, carla.TrafficLightState.Red)

    # 设置行人在模拟环境中的出现概率
    traffic_manager.set_global_percentage_of_walkers_percentage(30)  # 30%的概率生成行人

    # 让程序运行一段时间
    try:
        while True:
            world.tick()  # 更新世界状态
            time.sleep(1)  # 控制更新频率
    except KeyboardInterrupt:
        print("用户中断，退出程序。")
    finally:
        # 销毁生成的车辆
        for vehicle in vehicles:
            vehicle.destroy()
        print("所有车辆已销毁。")

if __name__ == '__main__':
    main()

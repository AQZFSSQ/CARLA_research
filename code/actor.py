import carla
import random
import time

def connect_to_carla(host='localhost', port=2000):
    client = carla.Client(host, port)
    client.set_timeout(10.0)
    
    # 载入地图1
    world = client.load_world('Town01')
    return world

def set_vehicle_properties(vehicle, speed=20, direction=(1, 0)):
    """
    设置车辆的速度和方向
    :param vehicle: 车辆对象
    :param speed: 目标速度（米/秒）
    :param direction: 方向向量
    """
    control = carla.VehicleControl()
    control.throttle = min(speed / 100, 1.0)  # 将速度限制在0到1之间
    vehicle.apply_control(control)

def set_walker_properties(walker, speed=1.5):
    """
    设置行人的速度
    :param walker: 行人对象
    :param speed: 目标速度（米/秒）
    """
    walker.set_target_velocity(carla.Vector3D(speed, 0, 0))

def spawn_vehicles(world, num_vehicles):
    # 获取蓝图库
    blueprint_library = world.get_blueprint_library()
    # 筛选出所有车辆蓝图
    vehicle_blueprints = blueprint_library.filter('vehicle.*')

    # 获取生成点并打乱顺序
    spawn_points = world.get_map().get_spawn_points()
    random.shuffle(spawn_points)

    vehicles = []  # 用于存储生成的车辆
    # 根据生成点数量和请求的车辆数量生成车辆
    for i in range(min(num_vehicles, len(spawn_points))):
        # 随机选择一个车辆蓝图
        blueprint = random.choice(vehicle_blueprints)
        # 获取对应的生成点
        transform = spawn_points[i]
        # 尝试在指定位置生成车辆
        vehicle = world.try_spawn_actor(blueprint, transform)
        if vehicle:  # 如果成功生成车辆
            vehicles.append(vehicle)  # 将车辆添加到列表中
            # 关闭自动驾驶功能
            vehicle.set_autopilot(False)
            set_vehicle_properties(vehicle, speed=20, direction=(1, 0))  # 设置车辆速度和方向
    
    return vehicles  # 返回生成的车辆列表

def spawn_walkers(world, num_walkers):
    # 获取蓝图库
    blueprint_library = world.get_blueprint_library()
    # 筛选出所有行人蓝图
    walker_blueprints = blueprint_library.filter('walker.pedestrian.*')

    walkers = []  # 用于存储生成的行人
    # 根据请求的行人数量生成行人
    for _ in range(num_walkers):
        # 随机选择一个行人蓝图
        blueprint = random.choice(walker_blueprints)
        # 获取一个随机的生成位置
        spawn_point = carla.Transform()
        spawn_point.location = world.get_random_location_from_navigation()
        # 尝试在指定位置生成行人
        walker = world.try_spawn_actor(blueprint, spawn_point)
        if walker:  # 如果成功生成行人
            walkers.append(walker)  # 将行人添加到列表中
            set_walker_properties(walker, speed=1.5)  # 设置行人速度
    
    return walkers  # 返回生成的行人列表

def main():
    world = connect_to_carla()

    # 用户输入生成数量
    num_vehicles = int(input("请输入要生成的车辆数量: "))
    num_walkers = int(input("请输入要生成的行人数量: "))

    vehicles = spawn_vehicles(world, num_vehicles)
    walkers = spawn_walkers(world, num_walkers)

    print(f"生成了 {len(vehicles)} 辆车辆和 {len(walkers)} 个行人。")

    time.sleep(60)

    # 清理生成的对象
    for vehicle in vehicles:
        vehicle.destroy()
    for walker in walkers:
        walker.destroy()

if __name__ == '__main__':
    main()

import carla
import random
import time
import math

# 控制车辆的函数，接受车辆对象、目标速度和转向值
def control_vehicle(vehicle, target_speed, steer):
    current_speed = get_speed(vehicle)  # 获取当前速度
    throttle = 0.0  # 油门初始值
    brake = 0.0  # 刹车初始值
    # 根据当前速度与目标速度的比较来调整油门或刹车
    if current_speed < target_speed:
        throttle = 0.5  # 如果当前速度小于目标速度，给油门
    else:
        brake = 0.3  # 如果当前速度大于等于目标速度，开始刹车
    # 应用控制指令
    vehicle.apply_control(carla.VehicleControl(throttle=throttle, brake=brake, steer=steer))

# 获取车辆当前速度的函数
def get_speed(vehicle):
    vel = vehicle.get_velocity()  # 获取车辆速度向量
    # 将速度从米每秒转换为公里每小时
    speed = 3.6 * math.sqrt(vel.x**2 + vel.y**2 + vel.z**2)
    return speed

# 计算两个位置之间的距离
def calculate_distance(location1, location2):
    dx = location1.x - location2.x  # x轴差值
    dy = location1.y - location2.y  # y轴差值
    dz = location1.z - location2.z  # z轴差值
    return math.sqrt(dx**2 + dy**2 + dz**2)  # 返回三维空间的距离

# 获取车辆与目标路径点之间的转向角度
def get_steering_angle(vehicle, waypoint):
    vehicle_transform = vehicle.get_transform()  # 获取车辆的变换信息
    v_begin = vehicle_transform.location  # 车辆起始位置
    # 计算车辆前进方向的结束位置
    v_end = vehicle_transform.location + carla.Location(
        x=math.cos(math.radians(vehicle_transform.rotation.yaw)),
        y=math.sin(math.radians(vehicle_transform.rotation.yaw))
    )
    w_location = waypoint.transform.location  # 获取路径点位置
    v_vec = [v_end.x - v_begin.x, v_end.y - v_begin.y]  # 车辆的方向向量
    w_vec = [w_location.x - v_begin.x, w_location.y - v_begin.y]  # 路径点的方向向量
    # 计算向量的点积和行列式
    dot = v_vec[0] * w_vec[0] + v_vec[1] * w_vec[1]
    det = v_vec[0] * w_vec[1] - v_vec[1] * w_vec[0]
    angle = math.atan2(det, dot)  # 计算转向角度
    return angle

def main():
    client = carla.Client('localhost', 2000)  # 连接CARLA服务器
    client.set_timeout(10.0)  # 设置超时时间

    world = client.load_world('Town01')  # 加载场景

    weather = carla.WeatherParameters.ClearNoon  # 设置天气为晴天
    world.set_weather(weather)

    blueprint_library = world.get_blueprint_library()  # 获取蓝图库

    vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))  # 随机选择车辆蓝图
    spawn_points = world.get_map().get_spawn_points()  # 获取生成点

    start_point = spawn_points[0]  # 选择第一个生成点
    vehicle = world.try_spawn_actor(vehicle_bp, start_point)  # 尝试生成车辆
    if vehicle is None:
        print("目标车辆生成失败")  # 如果生成失败，输出错误信息
        return
    print("目标车辆生成成功")  # 输出成功信息

    # 创建并管理相机传感器
    camera_bp = blueprint_library.find('sensor.camera.rgb')  # 找到RGB相机传感器的蓝图
    camera_transform = carla.Transform(carla.Location(x=-8.0, z=5.0))  # 设置相机的位置
    camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)  # 将相机附加到车辆上
    camera.listen(lambda image: image.save_to_disk('_out/%06d.png' % image.frame))  # 保存相机图像

    map = world.get_map()  # 获取地图
    waypoints = [map.get_waypoint(start_point.location)]  # 获取起始点的路径点
    # 生成路径点
    for _ in range(100):  # 增加路径长度
        next_waypoint = random.choice(waypoints[-1].next(2.0))  # 从当前路径点获取下一个路径点
        waypoints.append(next_waypoint)  # 将下一个路径点添加到路径列表中
        # 在世界中绘制路径点
        world.debug.draw_string(next_waypoint.transform.location, 'O', draw_shadow=False,
                                color=carla.Color(r=255, g=0, b=0), life_time=120.0,
                                persistent_lines=True)

    slow_vehicle_bp = random.choice(blueprint_library.filter('vehicle.*'))  # 随机选择缓速车辆的蓝图
    # 在路径的特定点生成缓速车辆
    for waypoint in waypoints[10:30]:  # 尝试路径的多个点
        slow_vehicle = world.try_spawn_actor(slow_vehicle_bp, waypoint.transform)  # 尝试生成缓速车辆
        if slow_vehicle is not None:
            print("缓速车辆生成成功")  # 如果生成成功，输出信息
            break
    else:
        print("缓速车辆生成失败")  # 如果生成失败，输出错误信息
        return

    slow_vehicle.set_autopilot(False)  # 关闭缓速车辆的自动驾驶
    slow_vehicle.apply_control(carla.VehicleControl(throttle=0.2))  # 让缓速车辆以低速行驶

    try:
        target_speed = 30  # 设置目标速度
        overtaking = False  # 超车标志

        while True:
            vehicle_location = vehicle.get_location()  # 获取车辆位置
            # 找到离车辆最近的路径点
            closest_waypoint = min(waypoints, key=lambda waypoint: calculate_distance(waypoint.transform.location, vehicle_location))
            steer = get_steering_angle(vehicle, closest_waypoint)  # 获取转向角度

            distance_to_slow_vehicle = calculate_distance(vehicle.get_location(), slow_vehicle.get_location())  # 计算与缓速车辆的距离

            # 判断是否需要进行超车
            if not overtaking and distance_to_slow_vehicle < 10.0:
                overtaking = True  # 设置超车标志
                target_speed = 50  # 提高目标速度以便超车

                # 模拟超车过程
                vehicle.apply_control(carla.VehicleControl(steer=-0.3))  # 向左转
                time.sleep(1)  # 等待一段时间
                vehicle.apply_control(carla.VehicleControl(steer=0.0))  # 直行
                time.sleep(2)  # 等待一段时间
                vehicle.apply_control(carla.VehicleControl(steer=0.3))  # 向右转
                time.sleep(1)  # 等待一段时间

                target_speed = 30  # 恢复目标速度
                overtaking = False  # 重置超车标志

            control_vehicle(vehicle, target_speed, steer)  # 控制车辆
            time.sleep(0.1)  # 等待一小段时间

    finally:
        # 确保相机和车辆被销毁
        if camera.is_alive:
            camera.stop()  # 停止相机
            camera.destroy()  # 销毁相机
        if vehicle.is_alive:
            vehicle.destroy()  # 销毁车辆
        if slow_vehicle.is_alive:
            slow_vehicle.destroy()  # 销毁缓速车辆

if __name__ == '__main__':
    main()  # 调用主函数

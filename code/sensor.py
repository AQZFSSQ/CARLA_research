import carla
import random
import struct
import os

def save_lidar_data(data, file_path):
    # 确保目录存在
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)

    # 打开文件准备写入
    with open(file_path, 'w') as f:
        # 写入标题行
        f.write("X, Y, Z, Intensity\n")
        
        for i in range(0, len(data.raw_data), 16):
            # 将原始数据解包为浮点数（XYZI）
            x, y, z, intensity = struct.unpack('ffff', data.raw_data[i:i+16])
            f.write(f"{x}, {y}, {z}, {intensity}\n")

def main():
    # 连接到Carla服务器
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)
    world = client.get_world()

    # 获取车辆蓝图
    blueprint_library = world.get_blueprint_library()
    vehicle_blueprint = random.choice(blueprint_library.filter('vehicle.*'))

    # 选择一个随机的生成点
    spawn_points = world.get_map().get_spawn_points()
    spawn_point = random.choice(spawn_points)

    # 生成目标车辆
    vehicle = world.spawn_actor(vehicle_blueprint, spawn_point)

    # 获取激光雷达蓝图
    lidar_blueprint = blueprint_library.find('sensor.lidar.ray_cast')

    # 配置激光雷达的参数
    lidar_blueprint.set_attribute('range', '50')  # 设置扫描范围为50米
    lidar_blueprint.set_attribute('rotation_frequency', '10')  # 每秒钟旋转10次
    lidar_blueprint.set_attribute('channels', '32')  # 设置激光束数量为32
    lidar_blueprint.set_attribute('points_per_second', '56000')  # 每秒扫描56000个点

    # 定义激光雷达的安装位置
    lidar_transform = carla.Transform(carla.Location(x=0, z=2.5))

    # 将激光雷达附加到车辆上
    lidar_sensor = world.spawn_actor(lidar_blueprint, lidar_transform, attach_to=vehicle)

    # 指定文件路径，包括文件名
    file_path = "C:\\Users\\16771\\Desktop\\Carla_photocollection\\lidar_data.txt"

    # 设定传感器数据的回调函数
    def lidar_callback(data):
        save_lidar_data(data, file_path)

    # 绑定回调函数
    lidar_sensor.listen(lidar_callback)

    try:
        # 使车辆自动驾驶
        vehicle.set_autopilot(True)
        # 运行一段时间
        world.wait_for_tick(10)
    finally:
        # 销毁传感器和车辆
        lidar_sensor.stop()
        lidar_sensor.destroy()
        vehicle.destroy()

if __name__ == '__main__':
    main()

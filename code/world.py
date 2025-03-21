#!/usr/bin/env python

import glob
import os
import sys
import carla
import random
import logging
import time

def set_weather(world):
    """设置天气条件"""
    weather_presets = {
        '1': ('ClearNoon', carla.WeatherParameters.ClearNoon),
        '2': ('CloudyNoon', carla.WeatherParameters.CloudyNoon),
        '3': ('WetNoon', carla.WeatherParameters.WetNoon),
        '4': ('HardRainNoon', carla.WeatherParameters.HardRainNoon),
        '5': ('WetCloudyNoon', carla.WeatherParameters.WetCloudyNoon)
    }

    print("请选择天气类型：")
    for key, (name, _) in weather_presets.items():
        print(f"{key}: {name}")

    choice = input("输入天气类型编号 (1-5): ")
    if choice in weather_presets:
        world.set_weather(weather_presets[choice][1])
        print(f"Weather set to: {weather_presets[choice][0]}")
    else:
        print("无效的选择，使用默认天气：ClearNoon")
        world.set_weather(carla.WeatherParameters.ClearNoon)

def set_map(client):
    """设置地图"""
    available_maps = client.get_available_maps()

    print("请选择地图：")
    for index, map_name in enumerate(available_maps, start=1):
        print(f"{index}: {map_name}")

    choice = input(f"输入地图编号 (1-{len(available_maps)}): ")
    try:
        map_index = int(choice) - 1
        if 0 <= map_index < len(available_maps):
            client.load_world(available_maps[map_index])
            print(f"Map set to: {available_maps[map_index]}")
        else:
            raise ValueError
    except (ValueError, IndexError):
        print("无效的选择，使用默认地图：Town01")
        client.load_world('Town01')

def spawn_vehicles(world, traffic_manager, num_vehicles=5):
    """生成正常行驶的车辆"""
    blueprint_library = world.get_blueprint_library()
    vehicle_blueprints = blueprint_library.filter('vehicle.*')
    spawn_points = world.get_map().get_spawn_points()
    random.shuffle(spawn_points)

    vehicles = []
    for i in range(num_vehicles):
        blueprint = random.choice(vehicle_blueprints)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        if i >= len(spawn_points):
            print("生成点不足，无法生成更多车辆。")
            break
        transform = spawn_points[i]
        vehicle = world.spawn_actor(blueprint, transform)
        vehicle.set_autopilot(True, traffic_manager.get_port())
        vehicles.append(vehicle)
        print(f"生成车辆 {vehicle.id} 于位置 {transform.location}")

    return vehicles

def update_spectator_view(world, vehicle):
    """更新观察者视角以跟随目标车辆"""
    spectator = world.get_spectator()
    vehicle_transform = vehicle.get_transform()
    spectator_transform = carla.Transform(vehicle_transform.location + carla.Location(x=0, y=0, z=20),
                                          carla.Rotation(pitch=-90))
    spectator.set_transform(spectator_transform)

def main():
    host = '127.0.0.1'
    port = 2000

    logging.basicConfig(format='%(levelname)s: %(message)s', level=logging.INFO)

    vehicles = []

    try:
        client = carla.Client(host, port)
        client.set_timeout(10.0)

        set_map(client)
        world = client.get_world()
        set_weather(world)

        traffic_manager = client.get_trafficmanager()
        traffic_manager.set_global_distance_to_leading_vehicle(2.5)

        vehicles = spawn_vehicles(world, traffic_manager, num_vehicles=5)
        if vehicles:
            target_vehicle = random.choice(vehicles)

            # 保持仿真运行以便观察车辆行驶
            while True:
                update_spectator_view(world, target_vehicle)
                world.wait_for_tick()

    except KeyboardInterrupt:
        print("\n用户中断，退出程序。")
    except Exception as e:
        logging.error(e)
    finally:
        # 清理生成的车辆
        for vehicle in vehicles:
            vehicle.destroy()
        print("所有车辆已销毁。")

if __name__ == '__main__':
    main()

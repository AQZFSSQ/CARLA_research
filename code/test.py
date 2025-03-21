import glob
import os
import sys
import carla
import random
import logging
import time
import queue
import numpy as np
import cv2

def set_weather(world):
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
    blueprint_library = world.get_blueprint_library()
    vehicle_blueprints = blueprint_library.filter('vehicle.*')
    spawn_points = world.get_map().get_spawn_points()
    random.shuffle(spawn_points)
    
    vehicles = []
    for i in range(min(num_vehicles, len(spawn_points))):
        blueprint = random.choice(vehicle_blueprints)
        if blueprint.has_attribute('color'):
            color = random.choice(blueprint.get_attribute('color').recommended_values)
            blueprint.set_attribute('color', color)
        transform = spawn_points[i]
        vehicle = world.spawn_actor(blueprint, transform)
        vehicle.set_autopilot(True)
        vehicle.apply_control(carla.VehicleControl(throttle=0.5))
        vehicles.append(vehicle)
        print(f"生成车辆 {vehicle.id} 于位置 {transform.location}")
    
    return vehicles

def attach_camera_to_vehicle(world, vehicle):
    blueprint_library = world.get_blueprint_library()
    camera_bp = blueprint_library.find('sensor.camera.rgb')
    camera_transform = carla.Transform(carla.Location(x=-5, z=2.5))
    camera = world.spawn_actor(camera_bp, camera_transform, attach_to=vehicle)
    return camera

def save_image(image, folder, filename):
    if not os.path.exists(folder):
        os.makedirs(folder)
    array = np.frombuffer(image.raw_data, dtype=np.uint8)
    array = array.reshape((image.height, image.width, 4))
    array = array[:, :, :3]
    cv2.imwrite(os.path.join(folder, filename), array)

def update_spectator_view(world, vehicle):
    spectator = world.get_spectator()
    transform = vehicle.get_transform()
    spectator_transform = carla.Transform(
        transform.location + carla.Location(x=-10, z=5),
        transform.rotation
    )
    spectator.set_transform(spectator_transform)

def main(output_folder="C:\\Users\\16771\\Desktop\\Carla_photocollection"):
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
            camera = attach_camera_to_vehicle(world, target_vehicle)

            image_queue = queue.Queue()
            camera.listen(image_queue.put)

            try:
                frame_number = 0
                while True:
                    world.tick()
                    update_spectator_view(world, target_vehicle)
                    image = image_queue.get()
                    filename = f"frame_{frame_number:04d}.png"
                    save_image(image, output_folder, filename)
                    print(f"Image saved as {os.path.join(output_folder, filename)}")
                    frame_number += 1
                    time.sleep(5)

            except KeyboardInterrupt:
                print("用户中断，退出程序。")

            finally:
                camera.destroy()
                print("摄像机已销毁。")

    except Exception as e:
        logging.error(e)

    finally:
        for vehicle in vehicles:
            vehicle.destroy()
        print("所有车辆已销毁。")

if __name__ == '__main__':
    main()
import carla

def remove_all_buildings(world):
    try:
        # 获取所有建筑物对象
        env_building_objs = world.get_environment_objects(carla.CityObjectLabel.Buildings)
        
        # 遍历并禁用建筑物
        for index in range(len(env_building_objs)):
            world.enable_environment_objects([env_building_objs[index].id], False)
        
        print("All buildings have been removed.")
    
    except KeyboardInterrupt:
        print("Operation interrupted.")

def main():
    # 连接到Carla服务器
    client = carla.Client('localhost', 2000)
    client.set_timeout(10.0)

    # 载入地图1
    map_name = 'Town01'  # 确认地图1的名称为'Town01'
    world = client.load_world(map_name)
    print(f"Loaded map: {map_name}")

    # 删除所有建筑物
   # remove_all_buildings(world)

if __name__ == '__main__':
    main()

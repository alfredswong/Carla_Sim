import glob
import os
import sys
try:
    sys.path.append(glob.glob('../carla/dist/carla-*%d.%d-%s.egg' % (
        sys.version_info.major,
        sys.version_info.minor,
        'win-amd64' if os.name == 'nt' else 'linux-x86_64'))[0])
except IndexError:
    pass
import carla

import random
import time
import numpy as np
import cv2

IM_WIDTH = 640
IM_HEIGHT = 480

# process image back to rgb
def process_img(image):
    i = np.array(image.raw_data)
    i2 = i.reshape((IM_HEIGHT, IM_WIDTH, 4))
    i3 = i2[:, :, :3]
    cv2.imshow("", i3)
    cv2.waitKey(1)
    return i3/255.0

def process_gnss(coordinates):
    print('Latitude {}'.format(coordinates.latitude))
    print('Longitude %f' % (coordinates.longitude))
    print("Altitude %f" % (coordinates.altitude))
    print()

# add all the actors - vehicles, sensors to destroy at the end
actor_list = []
try:
    client = carla.Client('localhost', 2000)
    client.set_timeout(2.0)

    world = client.get_world()

    blueprint_library = world.get_blueprint_library()
    
    # find tesla model 3!!
    bp = blueprint_library.filter('model3')[0]
    print(bp)
    
    # randomly choose spawn points from the available list
    spawn_point = random.choice(world.get_map().get_spawn_points())

    # add the actor to the world
    vehicle = world.spawn_actor(bp, spawn_point)
    
    # go straight at small speed
    vehicle.apply_control(carla.VehicleControl(throttle=1.0, steer=0.0))
    # vehicle.set_autopilot(True)  # if you just wanted some NPCs to drive.

    actor_list.append(vehicle)

    # https://carla.readthedocs.io/en/latest/cameras_and_sensors
    # get the blueprint for this sensor
    blueprint = blueprint_library.find('sensor.camera.rgb')
    # change the dimensions of the image
    blueprint.set_attribute('image_size_x', f'{IM_WIDTH}')
    blueprint.set_attribute('image_size_y', f'{IM_HEIGHT}')
    blueprint.set_attribute('fov', '110')

    # Adjust sensor relative to vehicle
    spawn_point = carla.Transform(carla.Location(x=0.5, z=1.7))
    sensor_cam = world.spawn_actor(blueprint, spawn_point, attach_to=vehicle)

    # add the GNSS sensor 
    blueprint = blueprint_library.find('sensor.other.gnss')
    spawn_point = carla.Transform(carla.Location(x=0.5, z=1.7))
    # spawn the sensor and attach to vehicle.
    sensor = world.spawn_actor(blueprint, spawn_point, attach_to=vehicle)

    # add sensor to list of actors
    actor_list.append(sensor)
    actor_list.append(sensor_cam)

    # do something with this sensor
    sensor_cam.listen(lambda data:process_img(data))
    sensor.listen(lambda data: process_gnss(data))

    time.sleep(10)

finally:
    print('destroying actors')
    for actor in actor_list:
        actor.destroy()
    print('done.')
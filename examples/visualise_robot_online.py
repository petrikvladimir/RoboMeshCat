#!/usr/bin/env python
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import time
from pathlib import Path
from robomeshcat.object import Object
from robomeshcat.scene import Scene

example_folder = Path(__file__).parent

scene = Scene()
box1 = Object.create_cuboid(lengths=[0.3] * 3, color=[1, 0, 0], texture=example_folder.joinpath('texture.png'))
scene.add_object(box1)
scene.add_object(Object.create_sphere(0.1, name='green_obj', color=[0, 1, 0]))
scene.add_object(Object.create_mesh(path_to_mesh=example_folder.joinpath('spade.obj'), scale=1e-3, name='spade'))

"Online - immediate rendering of the scene "
# scene.render()
# box1.pose[2, 3] = 2.
# scene.objects['green_obj'].pose[2, 3] = 1.
# time.sleep(5)
# scene.render()

"Render into the animation that is then shown in meshcat"
with scene.animation(fps=1):
    scene.render()
    box1.pose[2, 3] = 1.
    scene.objects['green_obj'].pose[2, 3] = 0.5
    scene.render()
    scene.camera_zoom = 0.4
    scene.render()
    scene.camera_zoom = 1.
    scene.render()

# # Video recording
# with scene.record_video(fps=1, filename='/tmp/vid.mp4'):
#     scene.render()
#     box1.pose[2, 3] = 2.
#     scene.render()
#

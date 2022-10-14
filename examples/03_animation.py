#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-14
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import time
import numpy as np
from pathlib import Path
from example_robot_data.robots_loader import PandaLoader
from robomeshcat import Scene, Robot

scene = Scene()

robot = Robot(urdf_path=PandaLoader().df_path, mesh_folder_path=Path(PandaLoader().model_path).parent.parent)
scene.add_robot(robot)

with scene.animation(fps=1):
    scene.render()  # first frame of the animation is robot pointing up
    # in the second frame let's change the configuration
    robot[3] = np.deg2rad(-90)
    scene.render()

    # then let's rotate camera around the robot for 10s;
    # note that setting camera will forbid user to rotate the scene
    t = np.linspace(0, 2 * np.pi, 10)
    for tt in t:
        scene.camera_pos[0] = np.sin(tt)
        scene.camera_pos[1] = np.cos(tt)
        scene.camera_pos[2] = 1
        scene.render()

    scene.reset_camera()  # resetting the camera will allow user interaction again
    scene.render()

time.sleep(5)

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

"Meshcat can also create animations, that you can rewind forward/backward in the browser. This example shows how to "
"create such an animation, by changing the configuration of the robot."

scene = Scene()
robot = Robot(urdf_path=PandaLoader().df_path, mesh_folder_path=Path(PandaLoader().model_path).parent.parent)
scene.add_robot(robot)

with scene.animation(fps=1):  # start the animation with the current scene
    scene.render()

    robot[3] = np.deg2rad(-90)  # modify the scene
    scene.render()  # store the changes in the frame and start new frame modifications

    robot.opacity = 0.2
    scene.render()

    robot.opacity = 1.
    scene.render()

    robot.color = [0, 0, 0.7]
    scene.render()

    # then let's rotate camera around the robot for 10s;
    # note that setting camera will forbid user to rotate the scene
    for tt in np.linspace(0, 2 * np.pi, 10):
        scene.camera_pos[0] = np.sin(tt)
        scene.camera_pos[1] = np.cos(tt)
        scene.camera_pos[2] = 1
        scene.render()

    scene.reset_camera()  # resetting the camera will allow user interaction again

time.sleep(5)  # we need some time to send the animation to the browser

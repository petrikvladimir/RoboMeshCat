#!/usr/bin/env python
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import time
from pathlib import Path
import numpy as np
from robomeshcat import Robot, Scene

"This example shows how to add and control robots online in the visualizer."
"Robots can be loaded from URDF; we will add multiple robots to show the visual/collision models of the robot."

"Example robot data package for the robot meshes and URDF, please install it with"
"conda install -c conda-forge example-robot-data"

"All elements are stored in Scene that is responsible for rendering them in the MeshCat"
scene = Scene()

from example_robot_data.robots_loader import PandaLoader as RobLoader

"Create the first robot and add it to the scene"
rob = Robot(urdf_path=RobLoader().df_path, mesh_folder_path=Path(RobLoader().model_path).parent.parent, name='visual')
scene.add_robot(rob)

"Modify the configuration of the robot"
input('Press enter to change configuration of the robot')
rob[3] = np.deg2rad(-90)  # access by joint id, you can also use scene['visual'][3] = ...
rob['panda_joint5'] = np.deg2rad(90)  # access by joint name, you can also use scene['visual']['panda_joint5'] = ...

input('Press enter to change the pose of the robot')
rob.pos[1] = -1

input('Press enter to change the color of the robot')
rob.color[0] = 1.

input('Press enter to add a new robot that shows collision model of the robot')

col = Robot(urdf_path=RobLoader().df_path, mesh_folder_path=Path(RobLoader().model_path).parent.parent,
            show_collision_models=True)
scene.add_robot(col)
col[:] = rob[:]  # use the same pose for the collision model

input('Press enter to hide visual model and exit')
rob.hide()

time.sleep(1.)  # note that some delay is needed to propagate all the changes

#!/usr/bin/env python
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import time
from pathlib import Path
import numpy as np
from robomeshcat import Robot, Scene
import pinocchio as pin

"All elements are stored in Scene that is responsible for rendering them in the MeshCat"
scene = Scene()

"Robots can be loaded from URDF; we will add three robots to show the visual/collision models of the robot and blue"
"robot - color defined in URDF is overwritten. We need example robot data package for the robot meshes and URDF"

from example_robot_data.robots_loader import PandaLoader

robot = PandaLoader()
scene.add_robot(Robot(urdf_path=robot.df_path, mesh_folder_path=Path(robot.model_path).parent.parent,
                      name='robot_visual'))
scene.add_robot(Robot(urdf_path=robot.df_path, mesh_folder_path=Path(robot.model_path).parent.parent,
                      name='robot_collision', show_collision_models=True))
scene.add_robot(Robot(urdf_path=robot.df_path, mesh_folder_path=Path(robot.model_path).parent.parent, name='robot_blue',
                      color=[0, 0, 0.5]))

scene['robot_visual'].pos[1] = 0
scene['robot_collision'].pos[1] = 1
scene['robot_blue'].pos[1] = 2
scene.render()
time.sleep(2.)

"The robot configuration can be update with joint name or it's index(es) in the kinematic tree"
r = scene['robot_visual']
r[3] = np.deg2rad(-90)
r['panda_joint3'] = np.deg2rad(-90)
scene['robot_collision'][:] = pin.randomConfiguration(scene['robot_collision'].model)
scene.render()
time.sleep(2.)

#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-11-10
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import numpy as np
from pathlib import Path
from example_robot_data.robots_loader import TalosFullLoader as TalosLoader
from example_robot_data.robots_loader import PandaLoader
from robomeshcat import Scene, Robot

scene = Scene()

panda = Robot(urdf_path=PandaLoader().df_path, mesh_folder_path=Path(PandaLoader().model_path).parent.parent)
scene.add_robot(panda)
panda.pos = [1, 0, 0]
panda[3] = -np.pi/2
panda[5] = np.pi/2

talos = Robot(urdf_path=TalosLoader().df_path, mesh_folder_path=Path(TalosLoader().model_path).parent.parent)
scene.add_robot(talos)
talos.pos[2] = 1.075

# with scene.animation(fps=30):
with scene.video_recording(filename='/tmp/teaser.mp4', fps=30):
    scene.camera_pos = [2, 0, 2.5]
    for t in np.linspace(0., 1., 60):
        talos['arm_right_1_joint'] = -t
        talos['arm_left_1_joint'] = t
        panda[0] = t
        panda[2] = t
        scene.render()

    for t in np.linspace(0, 2 * np.pi, 60):
        scene.camera_pos[0] = 2 * np.cos(t)
        scene.camera_pos[1] = 2 * np.sin(t)
        talos['head_1_joint'] = t
        scene.render()


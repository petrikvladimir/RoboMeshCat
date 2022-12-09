#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-12-8
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
import time

import numpy as np
from pathlib import Path
from example_robot_data.robots_loader import TalosFullLoader as TalosLoader
import pinocchio as pin
import torch
from robomeshcat import Scene, Robot, Human

scene = Scene()

smplx_models_path = str(Path(__file__).parent.joinpath('models').joinpath('smplx'))
pose = np.eye(4)
human_default_pose = pin.exp6(np.array([0, 0, 0, np.pi / 2, 0., 0.])).homogeneous
human_default_pose[2, 3] = -.2
human = Human(pose=human_default_pose.copy(), color=[0.6] * 3, model_path=smplx_models_path)

sad_face = torch.tensor([[-0.4969, -0.2114, 1.5251, 0.1503, 0.4488, 1.7344, 2.1032, -0.3620, -1.2451, 1.8487]])
smile_face = torch.tensor([[3.4081, -1.1111, -1.4181, 0.5018, 0.0286, -0.5347, -0.0042, 0.1118, -0.2230, -0.1172]])
neutral_face = torch.tensor([[-0.5131, 1.0546, 0.6059, -0.6452, 2.7049, 0.8512, 0.0777, 0.8451, -1.4651, 0.3700]])

human.add_morph(human.get_vertices(expression=sad_face))
human.add_morph(human.get_vertices(expression=smile_face))
human.add_morph(human.get_vertices(expression=neutral_face))
# add some dancing morph
human.add_morph(human.get_vertices(body_pose=torch.randn(human.smplx_model.body_pose.shape) * 0.1))
human.add_morph(human.get_vertices(body_pose=torch.randn(human.smplx_model.body_pose.shape) * 0.1))
human.add_morph(human.get_vertices(body_pose=torch.randn(human.smplx_model.body_pose.shape) * 0.1))
scene.add_object(human)

talos = Robot(urdf_path=TalosLoader().df_path, mesh_folder_path=Path(TalosLoader().model_path).parent.parent)
scene.add_robot(talos)
talos.pos[0] = 1.
talos.pos[2] = 1.075
talos.rot = pin.utils.rotate('z', np.deg2rad(-90))
talos.opacity = 0.

q1 = np.array(
    [0.57943216, -0.1309057, -0.75505065, 0.78430028, -0.61956061, -0.27349631, 0.13615252, 0.0711049, -0.03615876,
     0.49826378, 0.17217602, 0.50618769, 0.44123115, -0.02707293, -1.18121182, 0.30893653, 2.01942401, -2.13127587,
     -0.10865551, 0.30782173, -0.58293303, -0.23586322, 0.42843663, 0.3494325, 0.52727565, 0.50386685, -0.48822942,
     0.09145592, -0.6189864, -0.09982653, -0.33399487, -0.99386967, -0.78832615, 1.12503886, 0.4816953, -0.33853157,
     0.15645548, 0.77799908, 0.25617193, 0.92783777, -0.06406897, 1.03065562, 0.65546472, 0.28488222])

q2 = np.array(
    [0.67953954, -0.23498704, -0.30815908, 1.26050064, -0.75429557, 0.39308716, -0.09183746, -0.3519678, 0.6029438,
     1.92670204, -0.85517111, 0.31218583, 1.12134325, -0.08521749, -0.2414049, 0.41116012, 2.19232313, -0.13271861,
     0.13766665, 0.79690452, -0.64291739, -1.02337668, 0.74399798, 0.32299157, 0.25029159, 0.81949992, -0.4262274,
     0.61293056, 0.01760217, -2.08710036, 0.20761188, -0.27267571, 0.2487861, -0.8711323, -0.19324595, -0.19482248,
     0.06016944, 0.13445533, 1.02400687, 0.02380557, -0.13022461, 0.19958255, 0.60717046, 0.81290787])

q0 = np.zeros_like(q1)
scene.render()

with scene.animation(fps=1):
    scene.camera_pos = [0, -0.3, 0.2]
    scene.render()
    human.display_morph(0)
    scene.render()
    human.display_morph(1)
    scene.render()
    human.display_morph(2)
    human.pos[0] = -.5
    human.pos[2] = 1.3
    scene.camera_pos = [0, -2., 2.5]
    scene.render()
    talos.opacity = 1.
    scene.render()

    for _ in range(2):
        talos[:] = q1
        human.display_morph(3)
        scene.render()
        talos[:] = q2
        human.display_morph(4)
        scene.render()
        talos[:] = q0
        human.display_morph(5)
        scene.render()

    human.display_morph(None)
    human.pose = human_default_pose
    scene.camera_pos = [0, -0.3, 0.2]
    scene.render()

time.sleep(3.)

#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-11-30
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
from pathlib import Path
import numpy as np
import pinocchio as pin
import torch

from robomeshcat import Scene, Human

"This examples show how to use the human model and how to animate its pose and color. "
"We show three case studies: "
"(i) the first case study shows how to manipulate human online, i.e. without animation"
"(ii) this case study shows how to animate pose and color of the human in case of uniform color"
"(iii) this case study shows how use per vertex color of the human (only in online mode, no animation yet!)"

case_study = 2  # chose which case study to visualize
scene = Scene()
"Set smplx_models_path to the directory where are your SMPLX models"
smplx_models_path = str(Path(__file__).parent.joinpath('models').joinpath('smplx'))
human_default_pose = pin.exp6(np.array([0, 0, 0, np.pi / 2, 0., 0.])).homogeneous
human_default_pose[2, 3] = 1.2

if case_study == 0:
    "First let's create the human, arguments are forward to smplx constructor, so you can adjust the human model args"
    human = Human(pose=human_default_pose, color=[1., 0., 0.], model_path=smplx_models_path)
    scene.add_object(human)  # add human to the scene, it will be visualized immediately

    input('Press enter to change the body pose and shape of the human')
    human.smplx_model.body_pose.data += 0.1  # modify the pose
    human.smplx_model.betas.data += 0.1  # modify shape params
    human.smplx_model.expression.data += 0.1  # modify expression param
    human.update_vertices()  # recreate the geometry model to update in the viewer, this is allowed only in online use

    input('Press enter to change the color, opacity, and position of the human')
    human.pos[0] = 1.
    human.color = [0, 1, 0]
    human.opacity = 0.5
    input('Press enter to hide the model and exit.')
    human.hide()

elif case_study == 1:
    human = Human(pose=human_default_pose, color=[1., 0., 0.], model_path=smplx_models_path)

    # You need to create all the animation poses of the human in advance of adding the human to the scene
    # It's called morphologies of the pose
    human.smplx_model.betas.data += 1
    human.add_morph(human.get_vertices())  # the first morph changes the shape

    human.smplx_model.body_pose.data += 0.1
    human.add_morph(human.get_vertices())  # the second morp changes the body pose

    scene.add_object(human)  # add human to the scene, no morphology can be added/modified after this step

    "Let's animate"
    with scene.animation(fps=1):
        human.display_morph(None)  # this will display the human shape that is not affected by morphologies
        scene.render()

        human.display_morph(0)
        scene.render()

        human.display_morph(1)
        scene.render()

        human.color = [0, 0.8, 0]
        scene.render()

        # You can also change the .pos, .rot, .opacity, .visible, in animation
elif case_study == 2:
    # To have per vertex colors, use attribute use_vertex_colors=True
    human = Human(pose=human_default_pose, color=[1., 0., 0.], model_path=smplx_models_path, use_vertex_colors=True)
    scene.add_object(human)

    input('press enter to change colors to random')
    human.update_vertices(vertices_colors=np.random.rand(human.smplx_model.get_num_verts(), 3))

    input('press enter to change colors to blue')
    human.update_vertices(vertices_colors=[[0., 0., 0.75]] * human.smplx_model.get_num_verts())

    input('press enter to display wireframe')
    human._show_wireframe = True
    human.update_vertices(vertices_colors=[[0., 0., 0.]] * human.smplx_model.get_num_verts())

    input('sample new expressions and store them into video, rotate manually to see the face')
    # human.update_vertices(vertices=human.get_vertices(betas=torch.randn([1, 10])))
    human._show_wireframe = False
    human._vertex_colors[:] = 0.6
    with scene.video_recording(filename='/tmp/face_expression.mp4', fps=1):
        for _ in range(10):
            human.update_vertices(vertices=human.get_vertices(expression=torch.randn([1, 10])))
            scene.render()

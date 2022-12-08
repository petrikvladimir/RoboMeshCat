#!/usr/bin/env python
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import numpy as np
from pathlib import Path
from pinocchio.utils import rotate

from robomeshcat import Object, Scene

" This example shows how to update properties of the objects online - i.e., changes are apparent in the visualizer "
"immediately as they are set."

"All elements are stored in Scene that is responsible for rendering them in the MeshCat. "
scene = Scene()

"You can add objects into the scene and refer to them through the object instance or by the name"
obj1 = Object.create_sphere(radius=0.1, name='red_sphere', opacity=0.5, color=[1., 0., 0.])
scene.add_object(obj1)


"Let's set object position in z-axis, both options do the same"
input('Press enter to continue: to move sphere up')
obj1.pos[2] = 1.
scene['red_sphere'].pos[2] = 1.


"Other objects could be added to the scene too"
input('Press enter to continue: to add more objects')
scene.add_object(Object.create_cuboid(lengths=0.1, name='box', color=[1, 0, 0]))
scene.add_object(Object.create_cylinder(length=0.6, radius=0.1, name='cylinder'))
scene.add_object(Object.create_mesh(path_to_mesh=Path(__file__).parent.joinpath('spade.obj'), scale=1e-3, name='spade'))

scene['box'].pos[1] = 0.25  # other options: scene['box'].pos = [1, 1, 1], scene['box'].pose = ...
scene['cylinder'].pos[0] = -0.5
scene['cylinder'].rot = rotate('x', np.deg2rad(90))
scene['spade'].pos[1] = 0.75


"You can also adjust color, opacity, or visibility of the object."
input('Press enter to continue: to change the color and opacity')
scene['box'].color = [0, 1, 0]  # other options: scene['box'].color[1] = 1.
scene['box'].opacity = 0.5

input('Press enter to continue: to hide box and finis')
scene['box'].hide()  # other options: scene['box'].visible = False

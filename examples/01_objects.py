#!/usr/bin/env python
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import time
from pathlib import Path

import meshcat.geometry
import numpy as np

from robomeshcat import Object, Scene
from pinocchio.utils import rotate

example_folder = Path(__file__).parent

"All elements are stored in Scene that is responsible for rendering them in the MeshCat"
scene = Scene()

"You can objects into the scene and refer to them through the object instance or by the name"
obj1 = Object.create_sphere(radius=0.1, name='red_sphere', opacity=0.5, color=[1., 0., 0.])
scene.add_object(obj1)

"Let's set object position in z-axis, both options do the same"
obj1.pos[2] = 1.
scene['red_sphere'].pos[2] = 1.

"Now we can render the scene"
scene.render()
time.sleep(2.)

"Other objects could be added to the scene too"
scene.add_object(Object.create_cuboid(lengths=0.1, name='box', color=[1, 0, 0]))
scene.add_object(Object.create_cylinder(length=0.6, radius=0.1, name='cylinder'))
scene.add_object(Object.create_mesh(path_to_mesh=example_folder.joinpath('spade.obj'), scale=1e-3, name='spade'))

scene['box'].pos[1] = 0.25
scene['cylinder'].pos[1] = 0.5
scene['cylinder'].rot = rotate('x', np.deg2rad(90))
scene['spade'].pos[1] = 0.75

scene.render()
time.sleep(2.)

"In immediate rendering, you can also adjust the geometries/color/opacity and texture, but this will not work for "
"animations described below in which only the pose and camera can be updated."
scene['box'].color = [0, 1, 0]
scene['box'].opacity = 0.5
scene['box'].geometry = meshcat.geometry.Box([0.2] * 3)
scene.render()
time.sleep(2.)

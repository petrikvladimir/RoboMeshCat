#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-11-30
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
import time
from pathlib import Path

import numpy as np
import torch
from smplx import SMPLX
from smplx.utils import SMPLXOutput
import meshcat.geometry as g
import pinocchio as pin

from robomeshcat import Scene, Robot, Object, Human

human = Human(
    pose=pin.exp6(np.array([0, 0, 0, np.pi / 2, 0., 0.])).homogeneous,
    color=[1., 0., 0.],
    model_path=str(Path(__file__).parent.joinpath('models').joinpath('smplx')),
)
scene = Scene()

online = False

if online:
    " Online use of human "
    scene.add_object(human)  # add human to the scene
    scene.render()  # render default pose
    human.smplx_model.body_pose.data += 0.1  # modify the pose
    human.smplx_model.betas.data += 0.1  # modify shape params
    human.smplx_model.expression.data += 0.1  # modify expression param
    human.update_vertices()  # recreate the geometry model to update in the viewer
    scene.render()
else:
    " Animation use of human "
    # You need to create all the poses of the human in advance of adding the human to the scene
    human.smplx_model.betas.data = 0
    human.add_morph(human.get_vertices())
    human.smplx_model.betas.data = 1
    human.add_morph(human.get_vertices())

    scene.add_object(human)  # add human to the scene

    with scene.animation(fps=1):
        pass


print('a')

exit(1)


# human.add_morph()


class TriangularMeshGeometryWithMorphAttributes(g.TriangularMeshGeometry):
    def __init__(self, morph_positions=None, **kwargs):
        super(TriangularMeshGeometryWithMorphAttributes, self).__init__(**kwargs)
        self.morph_positions = morph_positions

    def lower(self, object_data):
        ret = super(TriangularMeshGeometryWithMorphAttributes, self).lower(object_data=object_data)
        ret[u"data"][u"morphAttributes"] = {u"position": [g.pack_numpy_array(pos.T) for pos in self.morph_positions]}
        return ret


model = SMPLX(
    model_path=str(Path(__file__).parent.joinpath('models').joinpath('smplx')),
    ext='npz', gender='neutral', num_betas=10, num_expression_coeffs=10, use_face_contour=False,
)


def get_vertices():
    betas = torch.randn([1, model.num_betas], dtype=torch.float32)
    expression = torch.randn([1, model.num_expression_coeffs], dtype=torch.float32)
    body_pose = torch.rand_like(model.body_pose)
    # body_pose = model.body_pose

    output: SMPLXOutput = model(betas=betas, expression=expression, body_pose=body_pose, return_verts=True)
    vertices = output.vertices.detach().cpu().numpy().squeeze()

    return vertices[::1]


vertices = get_vertices()
faces = model.faces
scene = Scene()
o = Object(
    TriangularMeshGeometryWithMorphAttributes(
        vertices=vertices, faces=faces, color=np.random.uniform(0, 1., size=vertices.shape),
        morph_positions=[get_vertices(), get_vertices()]
    )
)
o.rot = pin.exp3(np.array([np.pi / 2, 0., 0.]))  # @ pin.exp3(np.array([0., 0., np.pi / 2]))
o.pos[2] = -np.min(vertices[:, 1])
scene.add_object(o)

# scene.add_object(Object.create_cuboid([0.2] * 3, color=[1, 0, 0]))

with scene.animation(fps=1):
    with scene._animation.at_frame(scene.vis, next(scene._animation_frame_counter)) as f:
        # f['obj1']['<object>'].set_property('material.color', 'vector', [1, 0, 0])
        f['obj0']['<object>'].set_property('morphTargetInfluences', 'vector', [0, 0])

    with scene._animation.at_frame(scene.vis, next(scene._animation_frame_counter)) as f:
        # f['obj1']['<object>'].set_property('material.color', 'vector', [0, 1, 0])
        f['obj0']['<object>'].set_property('morphTargetInfluences', 'vector', [1, 0])

    with scene._animation.at_frame(scene.vis, next(scene._animation_frame_counter)) as f:
        # f['obj1']['<object>'].set_property('material.color', 'number', [0, 1, 0])
        f['obj0']['<object>'].set_property('morphTargetInfluences', 'vector', [0, 1])
#
# scene.vis['obj1']['<object>'].set_property('material.color.g', 1)

# print(scene.vis.window.get_scene())
# print(scene.vis.window.get_scene())

# scene.vis[o.name].set_property('.attributes.position', vertices.T.flatten().tolist())
# o1 = Object(
#     g.Points(
#         g.PointsGeometry(position=vertices.T, color=np.random.uniform(0., 1., size=vertices.T.shape)),
#         g.PointsMaterial(size=0.01)
#     )
# )
# o1.rot = pin.exp3(np.array([np.pi / 2, 0., 0.]))  # @ pin.exp3(np.array([0., 0., np.pi / 2]))
# o1.pos[2] = -np.min(vertices[:, 1])
# o1.pos[1] = 1.
# scene.add_object(o1)

scene.render()

time.sleep(5.)

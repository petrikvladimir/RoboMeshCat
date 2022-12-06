#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-12-6
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
from pathlib import Path
from typing import Optional, List, Union

import numpy as np
from meshcat import geometry as g

from . import Object


class Human(Object):

    def __init__(self, pose=None, color: Optional[List[float]] = None, opacity: float = 1., name: str = None,
                 texture: Optional[Union[g.ImageTexture, Path]] = None, **kwargs) -> None:
        from smplx import SMPLX
        self.smplx_model = SMPLX(**kwargs)
        super().__init__(None, pose, color, texture, opacity, name)
        self.update_vertices()  # this will create a geometry

    def get_vertices(self, **kwargs):
        """Return vertices of the mesh for the given smplx parameters."""
        output = self.smplx_model(return_verts=True, **kwargs)
        return output.vertices.detach().cpu().numpy().squeeze()

    def add_morph(self, vertices):
        """Add new morphology through which we can create animations."""
        self.geometry.morph_positions.append(vertices)

    def update_vertices(self, vertices=None):
        """Update vertices of the mesh will recreate the geometry. It cannot be used in animation for which you should
        use @add_morph"""
        self.geometry = TriangularMeshGeometryWithMorphAttributes(
            vertices=vertices() if vertices is not None else self.get_vertices(), faces=self.smplx_model.faces,
            morph_positions=[]
        )


class TriangularMeshGeometryWithMorphAttributes(g.TriangularMeshGeometry):
    def __init__(self, morph_positions=None, **kwargs):
        super(TriangularMeshGeometryWithMorphAttributes, self).__init__(**kwargs)
        self.morph_positions = morph_positions

    def lower(self, object_data):
        ret = super(TriangularMeshGeometryWithMorphAttributes, self).lower(object_data=object_data)
        ret[u"data"][u"morphAttributes"] = {u"position": [g.pack_numpy_array(pos.T) for pos in self.morph_positions]}
        return ret

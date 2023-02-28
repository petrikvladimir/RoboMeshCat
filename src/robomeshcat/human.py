#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-12-6
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
from __future__ import annotations

import numpy as np
from meshcat import geometry as g

from . import Object


class Human(Object):
    def __init__(
        self,
        pose=None,
        color: list[float] | None = None,
        opacity: float = 1.0,
        name: str | None = None,
        use_vertex_colors: bool = False,
        show_wireframe: bool = False,
        **kwargs,
    ) -> None:
        from smplx import SMPLX  # we import SMPLX here on purpose, so that smplx dependencies are optional

        self.smplx_model = SMPLX(**kwargs)
        super().__init__(None, pose, color if not use_vertex_colors else [1, 1, 1], None, opacity, name)

        self._use_vertex_colors = use_vertex_colors
        self._show_wireframe = show_wireframe
        clr = self._color_from_input(color)[np.newaxis, :]
        self._vertex_colors = np.repeat(clr, self.smplx_model.get_num_verts(), 0) if use_vertex_colors else None
        self.update_vertices(set_object=False)  # this will create a geometry

        "Additional properties that are modifiable "
        self._morph_target_influences = None

    @property
    def _material(self):
        mat = super()._material
        mat.wireframe = self._show_wireframe
        mat.vertexColors = self._use_vertex_colors
        return mat

    def get_vertices(self, **kwargs):
        """Return vertices of the mesh for the given smplx parameters."""
        output = self.smplx_model(return_verts=True, **kwargs)
        return output.vertices.detach().cpu().numpy().squeeze()

    def update_vertices(self, vertices=None, vertices_colors=None, set_object=True):
        if self._is_animation():
            print(
                'Update vertices of the mesh will recreate the geometry. It cannot be used in animation for '
                'which you should use this.add_morph function'
            )
            return
        self._geometry = TriangularMeshGeometryWithMorphAttributes(
            vertices=np.asarray(vertices) if vertices is not None else self.get_vertices(),
            faces=self.smplx_model.faces,
            color=np.asarray(vertices_colors) if vertices_colors is not None else self._vertex_colors,
            morph_positions=[],
            morph_colors=[],
        )
        if set_object:
            self._set_object()

    def add_morph(self, vertices, vertex_colors=None):
        """Add new morphology through which we can create animations."""
        self._geometry.morph_positions.append(vertices)
        if vertex_colors is not None:
            self._geometry.morph_colors.append(np.asarray(vertex_colors))

    def display_morph(self, morph_id):
        """Set morphTargetInfluences to display only the given morph_id."""
        self._morph_target_influences = [0] * self._geometry.number_of_morphs()
        if morph_id is not None:
            self._morph_target_influences[morph_id] = 1

    def _set_morph_property(self):
        if self._morph_target_influences is None:
            self._morph_target_influences = [0] * len(self._geometry.morph_positions)
        self._set_property('morphTargetInfluences', self._morph_target_influences, 'vector')

    def _reset_all_properties(self):
        super()._reset_all_properties()
        self._set_morph_property()


class TriangularMeshGeometryWithMorphAttributes(g.TriangularMeshGeometry):
    def __init__(self, morph_positions=None, morph_colors=None, **kwargs):
        super(TriangularMeshGeometryWithMorphAttributes, self).__init__(**kwargs)
        self.morph_positions = morph_positions
        self.morph_colors = morph_colors

    def number_of_morphs(self) -> int:
        return max(len(self.morph_colors), len(self.morph_positions))

    def lower(self, object_data):
        ret = super(TriangularMeshGeometryWithMorphAttributes, self).lower(object_data=object_data)
        ret[u"data"][u"morphAttributes"] = {}
        if self.morph_positions is not None:
            ret[u"data"][u"morphAttributes"][u"position"] = [g.pack_numpy_array(pos.T) for pos in self.morph_positions]
        if self.morph_colors is not None:
            ret[u"data"][u"morphAttributes"][u"color"] = [g.pack_numpy_array(c.T) for c in self.morph_colors]
        return ret

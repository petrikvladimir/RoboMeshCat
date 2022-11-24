#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#


import itertools
from pathlib import Path
from typing import List, Optional, Union
import trimesh
import numpy as np
import meshcat.geometry as g


class Object:
    """ Represent an object with arbitrary geometry that can be rendered in the meshcat. """

    id_iterator = itertools.count()

    def __init__(self, geometry=None, pose=None,
                 color: Optional[List[float]] = None, texture: Optional[Union[g.ImageTexture, Path]] = None,
                 opacity: float = 1., name: str = None) -> None:
        """ Create an object with given geometry, pose, color and opacity.
        :param geometry
        :param pose - 4x4 pose of the object
        :param color - RGB color of the object either tuple of integers [0-255] or tuple of floats [0. - 1.]
        :param texture - alternative to color, you can specify texture that object uses to render as meshcat texture or
            as a path to png file.
        :param opacity - transparency of the object from 0. to 1.
        :param name - unique name of the object, it's created automatically if not specified
        """
        super().__init__()
        self.name = f'obj{next(self.id_iterator)}' if name is None else name
        self.pose = np.eye(4) if pose is None else pose
        self.geometry = geometry

        self.color = color if color is not None else np.random.uniform(0, 1, 3)
        self.texture = g.ImageTexture(g.PngImage.from_file(texture)) if isinstance(texture, (Path, str)) else texture
        self.opacity = opacity

    @property
    def material(self):
        if self.texture is not None:
            return g.MeshLambertMaterial(map=self.texture, opacity=self.opacity)
        color = np.asarray(self.color).copy()
        if not (np.any(color > 1) and color.dtype == np.int):
            color *= 255
        color = np.clip(color, 0, 255)
        return g.MeshLambertMaterial(color=int(color[0]) * 256 ** 2 + int(color[1]) * 256 + int(color[2]),
                                     opacity=self.opacity)

    def is_material_equal(self, other):
        return np.all(np.isclose(self.color, other.color)) and self.texture == other.texture and np.isclose(
            self.opacity, other.opacity)

    @property
    def pos(self):
        return self.pose[:3, 3]

    @pos.setter
    def pos(self, p):
        self.pose[:3, 3] = p

    @property
    def rot(self):
        return self.pose[:3, :3]

    @rot.setter
    def rot(self, r):
        self.pose[:3, :3] = r

    @classmethod
    def create_cuboid(cls, lengths: Union[List[float], float], pose=None, color: Optional[List[float]] = None,
                      texture: Optional[Union[g.ImageTexture, Path]] = None, opacity: float = 1., name: str = None):
        """Create cuboid with a given size. """
        return cls(g.Box(lengths=[lengths] * 3 if isinstance(lengths, (float, int)) else lengths), pose=pose,
                   color=color, texture=texture, opacity=opacity, name=name)

    @classmethod
    def create_sphere(cls, radius: float, pose=None, color: Optional[List[float]] = None,
                      texture: Optional[Union[g.ImageTexture, Path]] = None, opacity: float = 1., name: str = None):
        """Create a sphere with a given radius. """
        return cls(g.Sphere(radius=radius), pose=pose, color=color, texture=texture, opacity=opacity, name=name)

    @classmethod
    def create_cylinder(cls, radius: float, length: float, pose=None, color: Optional[List[float]] = None,
                        texture: Optional[Union[g.ImageTexture, Path]] = None, opacity: float = 1., name: str = None):
        """Create a cylinder with a given radius and length. The axis of rotational symmetry is aligned with the z-axis
        that is common in robotics. To achieve that, we create a mesh of a cylinder instead of using meshcat cylinder
        that is aligned with y-axis. """
        mesh: trimesh.Trimesh = trimesh.creation.cylinder(radius=radius, height=length, sections=50)
        exp_obj = trimesh.exchange.obj.export_obj(mesh)
        return cls(g.ObjMeshGeometry.from_stream(trimesh.util.wrap_as_stream(exp_obj)), pose=pose, color=color,
                   texture=texture, opacity=opacity, name=name)

    @classmethod
    def create_mesh(cls, path_to_mesh: Union[str, Path], scale: Union[float, List[float]] = 1., pose=None,
                    color: Optional[List[float]] = None, texture: Optional[Union[g.ImageTexture, Path]] = None,
                    opacity: float = 1., name: str = None):
        """ Create a object given by mesh geometry loaded by trimes. """
        mesh: trimesh.Trimesh = trimesh.load(path_to_mesh, force='mesh')
        mesh.apply_scale(scale)
        try:
            exp_obj = trimesh.exchange.obj.export_obj(mesh)
        except ValueError:
            exp_obj = trimesh.exchange.obj.export_obj(mesh, include_texture=False)
        return cls(g.ObjMeshGeometry.from_stream(trimesh.util.wrap_as_stream(exp_obj)), pose=pose, color=color,
                   texture=texture, opacity=opacity, name=name)

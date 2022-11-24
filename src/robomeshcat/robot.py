#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-13
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
import itertools
from pathlib import Path
from typing import Union, Dict, Optional, List

import numpy as np
import pinocchio as pin

from .object import Object


class Robot:
    id_iterator = itertools.count()

    def __init__(self, urdf_path: Union[Path, str], mesh_folder_path: Union[Path, str, List[Path], List[str]] = None,
                 show_collision_models: bool = False, name: str = None, color: Optional[List[float]] = None,
                 opacity: Optional[float] = None, pose=None) -> None:
        """
        Create a robot from URDF using pinocchio loader.
        :param urdf_path: path to the urdf file that contains robot description
        :param mesh_folder_path: either a single path to the directory of meshes or list of paths to meshes directory,
          it's set to directory of urdf_path file by default
        :param show_collision_models: weather to show collision model instead of visual model
        :param name: name of the robot used in meshcat tree
        :param color: optional color that overwrites one from the urdf
        :param opacity: optional opacity that overwrites one from the urdf
        """
        super().__init__()
        self.name = f'robot{next(self.id_iterator)}' if name is None else name
        self.color = color
        self.opacity = opacity
        if mesh_folder_path is None:
            mesh_folder_path = str(Path(urdf_path).parent)  # by default use the urdf parent directory
        elif isinstance(mesh_folder_path, Path):
            mesh_folder_path = str(mesh_folder_path)
        elif isinstance(mesh_folder_path, list) and any((isinstance(path, Path) for path in mesh_folder_path)):
            mesh_folder_path = [str(path) for path in mesh_folder_path]
        self.model, col_model, vis_model = pin.buildModelsFromUrdf(str(urdf_path), mesh_folder_path)
        self.data, col_data, vis_data = pin.createDatas(self.model, col_model, vis_model)
        self.geom_model: pin.GeometryModel = col_model if show_collision_models else vis_model
        self.geom_data: pin.GeometryData = col_data if show_collision_models else vis_data

        self.pose = np.eye(4) if pose is None else pose
        self._q = pin.neutral(self.model)
        self.objects: Dict[str, Object] = {}
        self._init_objects()
        self.fk()

    def fk(self):
        """Compute ForwardKinematics and update the objects poses."""
        pin.forwardKinematics(self.model, self.data, self._q)
        pin.updateGeometryPlacements(self.model, self.data, self.geom_model, self.geom_data)
        base = pin.SE3(self.pose)
        for g, f in zip(self.geom_model.geometryObjects, self.geom_data.oMg):  # type: pin.GeometryObject, pin.SE3
            self.objects[f'{self.name}/{g.name}'].pose = (base * f).homogeneous

    def _init_objects(self):
        """Fill in objects dictionary based on the data from pinocchio"""
        for g in self.geom_model.geometryObjects:  # type: pin.GeometryObject
            kwargs = dict(
                name=f'{self.name}/{g.name}',
                color=g.meshColor[:3] if self.color is None else self.color,
                opacity=g.meshColor[3] if self.opacity is None else self.opacity,
                texture=g.meshTexturePath if g.meshTexturePath else None
            )
            if g.meshPath == 'BOX':
                self.objects[kwargs['name']] = Object.create_cuboid(lengths=2 * g.geometry.halfSide, **kwargs)
            elif g.meshPath == 'SPHERE':
                self.objects[kwargs['name']] = Object.create_sphere(radius=g.geometry.radius, **kwargs)
            elif g.meshPath == 'CYLINDER':
                r, l = g.geometry.radius, 2 * g.geometry.halfLength
                self.objects[kwargs['name']] = Object.create_cylinder(radius=r, length=l, **kwargs)
            else:
                self.objects[kwargs['name']] = Object.create_mesh(path_to_mesh=g.meshPath, scale=g.meshScale, **kwargs)

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

    def __getitem__(self, key):
        jid = self.model.getJointId(key) if isinstance(key, str) else key
        return self._q[jid]

    def __setitem__(self, key, value):
        jid = self.model.getJointId(key) if isinstance(key, str) else key
        self._q[jid] = value

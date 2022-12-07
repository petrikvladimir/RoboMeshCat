#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-13
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
import itertools
from pathlib import Path
from typing import Union, Dict, Optional, List, Tuple

import numpy as np
import pinocchio as pin

from .object import Object, ArrayWithCallbackOnSetItem


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
        self._model, self._data, self._geom_model, self._geom_data = self._build_model_from_urdf(
            urdf_path, mesh_folder_path, show_collision_models
        )

        """ Adjustable properties """
        self._pose = ArrayWithCallbackOnSetItem(np.eye(4) if pose is None else pose, cb=self._fk)
        self._q = ArrayWithCallbackOnSetItem(pin.neutral(self._model), cb=self._fk)
        self._color = ArrayWithCallbackOnSetItem(Object._color_from_input(color), cb=self._color_reset_on_set_item)
        self._opacity = opacity
        self._visible = True

        """Set of objects used to visualize the links."""
        self._objects: Dict[str, Object] = {}
        self._init_objects(overwrite_color=color is not None)

    @staticmethod
    def _build_model_from_urdf(urdf_path, mesh_folder_path, show_collision_models) -> Tuple[
        pin.Model, pin.Data, pin.GeometryModel, pin.GeometryData]:
        """Use pinocchio to load models and datas used for the visualizer."""
        if mesh_folder_path is None:
            mesh_folder_path = str(Path(urdf_path).parent)  # by default use the urdf parent directory
        elif isinstance(mesh_folder_path, Path):
            mesh_folder_path = str(mesh_folder_path)
        elif isinstance(mesh_folder_path, list) and any((isinstance(path, Path) for path in mesh_folder_path)):
            mesh_folder_path = [str(path) for path in mesh_folder_path]

        model, col_model, vis_model = pin.buildModelsFromUrdf(str(urdf_path), mesh_folder_path)
        data, col_data, vis_data = pin.createDatas(model, col_model, vis_model)
        geom_model: pin.GeometryModel = col_model if show_collision_models else vis_model
        geom_data: pin.GeometryData = col_data if show_collision_models else vis_data
        return model, data, geom_model, geom_data

    def _fk(self):
        """Compute ForwardKinematics and update the objects poses."""
        pin.forwardKinematics(self._model, self._data, self._q)
        pin.updateGeometryPlacements(self._model, self._data, self._geom_model, self._geom_data)
        base = pin.SE3(self._pose)
        for g, f in zip(self._geom_model.geometryObjects, self._geom_data.oMg):  # type: pin.GeometryObject, pin.SE3
            self._objects[f'{self.name}/{g.name}'].pose = (base * f).homogeneous

    def _init_objects(self, overwrite_color=False):
        """Fill in objects dictionary based on the data from pinocchio"""
        pin.forwardKinematics(self._model, self._data, self._q)
        pin.updateGeometryPlacements(self._model, self._data, self._geom_model, self._geom_data)
        base = pin.SE3(self._pose)
        for g, f in zip(self._geom_model.geometryObjects, self._geom_data.oMg):  # type: pin.GeometryObject, pin.SE3
            kwargs = dict(
                name=f'{self.name}/{g.name}',
                color=g.meshColor[:3] if not overwrite_color else self._color,
                opacity=g.meshColor[3] if self._opacity is None else self._opacity,
                texture=g.meshTexturePath if g.meshTexturePath else None,
                pose=(base * f).homogeneous
            )
            if g.meshPath == 'BOX':
                self._objects[kwargs['name']] = Object.create_cuboid(lengths=2 * g.geometry.halfSide, **kwargs)
            elif g.meshPath == 'SPHERE':
                self._objects[kwargs['name']] = Object.create_sphere(radius=g.geometry.radius, **kwargs)
            elif g.meshPath == 'CYLINDER':
                r, l = g.geometry.radius, 2 * g.geometry.halfLength
                self._objects[kwargs['name']] = Object.create_cylinder(radius=r, length=l, **kwargs)
            else:
                self._objects[kwargs['name']] = Object.create_mesh(path_to_mesh=g.meshPath, scale=g.meshScale, **kwargs)

    """ === Methods for adjusting the base pose of the robot. ==="""

    @property
    def pose(self):
        return self._pose

    @pose.setter
    def pose(self, v):
        self._pose[:, :] = v

    @property
    def pos(self):
        return self._pose[:3, 3]

    @pos.setter
    def pos(self, p):
        self._pose[:3, 3] = p

    @property
    def rot(self):
        return self._pose[:3, :3]

    @rot.setter
    def rot(self, r):
        self._pose[:3, :3] = r

    def __getitem__(self, key):
        jid = self._model.getJointId(key) if isinstance(key, str) else key
        return self._q[jid]

    def __setitem__(self, key, value):
        jid = self._model.getJointId(key) if isinstance(key, str) else key
        self._q[jid] = value

    """=== Control of the object visibility ==="""

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        self._visible = bool(v)
        for o in self._objects.values():
            o.visible = self._visible

    def hide(self):
        self.visible = False

    def show(self):
        self.visible = True

    """=== Control of the object transparency ==="""

    @property
    def opacity(self):
        return self._opacity

    @opacity.setter
    def opacity(self, v):
        self._opacity = v
        for o in self._objects.values():
            o.opacity = self._opacity

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, v):
        self._color = Object._color_from_input(v)
        self._color_reset_on_set_item()

    def _color_reset_on_set_item(self):
        for o in self._objects.values():
            o.color = self._color

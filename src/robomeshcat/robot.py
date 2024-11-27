#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-13
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
from __future__ import annotations

import itertools
from pathlib import Path

import numpy as np
import pinocchio as pin

from .object import Object, ArrayWithCallbackOnSetItem


class Robot:
    id_iterator = itertools.count()

    def __init__(
        self,
        urdf_path: Path | str | None = None,
        mesh_folder_path: Path | str | list[Path] | list[str] | None = None,
        pinocchio_model: pin.Model | None = None,
        pinocchio_data: pin.Data | None = None,
        pinocchio_geometry_model: pin.GeometryModel | None = None,
        pinocchio_geometry_data: pin.GeometryData | None = None,
        show_collision_models: bool = False,
        name: str | None = None,
        color: list[float] | None = None,
        opacity: float | None = None,
        pose=None,
    ) -> None:
        """
        Create a robot using pinocchio loader, you have to option to create a robot: (i) using URDF or
        (ii) using pinocchio models and data.
        :param urdf_path: path to the urdf file that contains robot description
        :param mesh_folder_path: either a single path to the directory of meshes or list of paths to meshes directory,
          it's set to directory of urdf_path file by default
        :param pinocchio_model, pinocchio_data, pinocchio_geometry_model, pinocchio_geometry_data: alternativelly, you
          can use pinocchio model instead of the urdf_path to construct the robot instance, either urdf_path or
          pinocchio_{model, data, geometry_model, geometry_data} has to be specified.
        :param show_collision_models: weather to show collision model instead of visual model
        :param name: name of the robot used in meshcat tree
        :param color: optional color that overwrites one from the urdf
        :param opacity: optional opacity that overwrites one from the urdf
        """
        super().__init__()
        self.name = f'robot{next(self.id_iterator)}' if name is None else name
        pin_not_defined = (
            pinocchio_model is None
            and pinocchio_data is None
            and pinocchio_geometry_model is None
            and pinocchio_geometry_data is None
        )
        assert urdf_path is None or pin_not_defined, 'You need to specify either urdf or pinocchio, not both.'
        if pin_not_defined:
            self._model, self._data, self._geom_model, self._geom_data = self._build_model_from_urdf(
                urdf_path, mesh_folder_path, show_collision_models
            )
        else:
            self._model, self._data = pinocchio_model, pinocchio_data
            self._geom_model, self._geom_data = pinocchio_geometry_model, pinocchio_geometry_data

        """ Adjustable properties """
        self._pose = ArrayWithCallbackOnSetItem(np.eye(4) if pose is None else pose, cb=self._fk)
        self._q = ArrayWithCallbackOnSetItem(pin.neutral(self._model), cb=self._fk)
        self._color = ArrayWithCallbackOnSetItem(Object._color_from_input(color), cb=self._color_reset_on_set_item)
        self._opacity = opacity
        self._visible = True

        """Set of objects used to visualize the links."""
        self._objects: dict[str, Object] = {}
        self._init_objects(overwrite_color=color is not None)

    @staticmethod
    def _build_model_from_urdf(
        urdf_path, mesh_folder_path, show_collision_models
    ) -> tuple[pin.Model, pin.Data, pin.GeometryModel, pin.GeometryData]:
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
        for g, f in zip(self._geom_model.geometryObjects, self._geom_data.oMg):
            self._objects[f'{self.name}/{g.name}'].pose = (base * f).homogeneous

    def _init_objects(self, overwrite_color=False):
        """Fill in objects dictionary based on the data from pinocchio"""
        pin.forwardKinematics(self._model, self._data, self._q)
        pin.updateGeometryPlacements(self._model, self._data, self._geom_model, self._geom_data)
        base = pin.SE3(self._pose)
        for g, f in zip(self._geom_model.geometryObjects, self._geom_data.oMg):
            kwargs = dict(
                name=f'{self.name}/{g.name}',
                color=g.meshColor[:3] if not overwrite_color else self._color,
                opacity=g.meshColor[3] if self._opacity is None else self._opacity,
                texture=g.meshTexturePath if g.meshTexturePath else None,
                pose=(base * f).homogeneous,
            )
            if g.meshPath == 'BOX':
                self._objects[kwargs['name']] = Object.create_cuboid(lengths=2 * g.geometry.halfSide, **kwargs)
            elif g.meshPath == 'SPHERE':
                self._objects[kwargs['name']] = Object.create_sphere(radius=g.geometry.radius, **kwargs)
            elif g.meshPath == 'CYLINDER':
                radius, length = g.geometry.radius, 2 * g.geometry.halfLength
                self._objects[kwargs['name']] = Object.create_cylinder(radius=radius, length=length, **kwargs)
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

    def _get_joint_id(self, key: str | int):
        """Get the joint id either from joint name or integer. The universe joint is
        not counted as we assume it is fixed."""
        if isinstance(key, int):
            return key
        jid = self._model.getJointId(key)
        # there is often universe joint that is not counted, so we need to adjust the
        # index
        if len(self._model.names) == len(self._q) + 1:
            jid -= 1
        return jid

    def __getitem__(self, key):
        return self._q[self._get_joint_id(key)]

    def __setitem__(self, key, value):
        self._q[self._get_joint_id(key)] = value

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

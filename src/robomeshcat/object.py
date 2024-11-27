#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

from __future__ import annotations

import itertools
from pathlib import Path
import trimesh
import numpy as np
from PIL import Image
import io
import meshcat.geometry as g
from meshcat.animation import AnimationFrameVisualizer


class Object:
    """Represent an object with arbitrary geometry that can be rendered in the meshcat."""

    id_iterator = itertools.count()

    def __init__(
        self,
        geometry=None,
        pose=None,
        color: list[float] | None = None,
        texture: g.ImageTexture | Path | None = None,
        opacity: float = 1.0,
        name: str | None = None,
    ) -> None:
        """Create an object with given geometry, pose, color and opacity.
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
        self._vis = None  # either a visualization tree or the frame of the animation, is set by the scene

        "List of properties that could be updated for all objects"
        self._pose = ArrayWithCallbackOnSetItem(np.eye(4) if pose is None else pose, cb=self._set_transform)
        self._color = ArrayWithCallbackOnSetItem(self._color_from_input(color), cb=self._color_reset_on_set_item)
        self._opacity = opacity
        self._visible = True

        "Not updatable properties."
        self._texture = g.ImageTexture(g.PngImage.from_file(texture)) if isinstance(texture, (Path, str)) else texture
        self._geometry = geometry

    @staticmethod
    def _color_from_input(clr: list[float] | np.ndarray | None, default=None):
        """Modify input color to always be represented by numpy array with values from 0 to 1"""
        if clr is None:
            clr = np.random.uniform(0, 1, 3) if default is None else default
        clr = np.asarray(clr)
        assert clr.shape == (3,)
        if np.any(clr > 1) and clr.dtype == np.int:
            clr = clr.astype(dtype=np.float) / 255
        clr = clr.clip(0.0, 1.0)
        return clr

    def _set_vis(self, vis):
        """Set visualizer. Used internally to create frames of animation."""
        self._vis = vis[self.name]

    def _assert_vis(self):
        assert (
            self._vis is not None
        ), 'The properties of the object cannot be modified unless object is added to the scene.'

    def _set_object(self):
        """Create an object in meshcat and set all the initial properties."""
        self._assert_vis()
        self._vis.set_object(self._geometry, self._material)
        self._set_transform()

    def _delete_object(self):
        """Delete an object from meshcat."""
        self._vis.delete()

    def _set_transform(self):
        """Update transformation in the meshcat."""
        self._assert_vis()
        self._vis.set_transform(self._pose)

    def _set_property(self, key, value, prop_type='number', subpath='<object>'):
        """Set property of the object, handle animation frames set_property internally."""
        self._assert_vis()
        element = self._vis if subpath is None else self._vis[subpath]
        if self._is_animation():
            element.set_property(key, prop_type, value)
        else:
            element.set_property(key, value)

    def _is_animation(self):
        """Return true if rendering to the animation. Used internally to modify the way of assigning properties until
        PR https://github.com/rdeits/meshcat/pull/137 is merged."""
        return isinstance(self._vis, AnimationFrameVisualizer)

    @property
    def _material(self):
        if isinstance(self._geometry, g.Object):
            return None
        if self._texture is not None:
            return g.MeshLambertMaterial(map=self._texture, opacity=self.opacity)
        color = self.color.copy() * 255
        color = np.clip(color, 0, 255)
        return g.MeshLambertMaterial(
            color=int(color[0]) * 256**2 + int(color[1]) * 256 + int(color[2]), opacity=self.opacity
        )

    """=== Control of the pose ==="""

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

    """=== Control of the object visibility ==="""

    @property
    def visible(self):
        return self._visible

    @visible.setter
    def visible(self, v):
        self._visible = bool(v)
        self._set_property('visible', value=self._visible, prop_type='boolean')

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
        if self._is_animation():
            self._set_property('material.opacity', value=self._opacity, prop_type='number')
        else:
            self._set_object()  # only way how to update opacity online is to reset the object

    @property
    def color(self):
        return self._color

    @color.setter
    def color(self, v):
        self._color[:] = self._color_from_input(v)

    def _color_reset_on_set_item(self):
        if self._is_animation():
            self._set_property('material.color', value=self.color.tolist(), prop_type='vector')
        else:
            self._set_object()  # only way how to update color online is to reset the object

    def _reset_all_properties(self):
        """Reset all properties in the meshcat, i.e. call setters with the same variable. Useful for the animation
        frames."""
        self.pose = self.pose
        self.color = self.color
        self.opacity = self.opacity
        self.visible = self.visible

    """=== Helper functions to create basic primitives ==="""

    @classmethod
    def create_cuboid(
        cls,
        lengths: list[float] | float,
        pose=None,
        color: list[float] | None = None,
        texture: g.ImageTexture | Path | None = None,
        opacity: float = 1.0,
        name: str | None = None,
    ):
        """Create cuboid with a given size."""
        box = g.Box(lengths=[lengths] * 3 if isinstance(lengths, (float, int)) else lengths)
        return cls(box, pose=pose, color=color, texture=texture, opacity=opacity, name=name)

    @classmethod
    def create_sphere(
        cls,
        radius: float,
        pose=None,
        color: list[float] | None = None,
        texture: g.ImageTexture | Path | None = None,
        opacity: float = 1.0,
        name: str | None = None,
    ):
        """Create a sphere with a given radius."""
        return cls(g.Sphere(radius=radius), pose=pose, color=color, texture=texture, opacity=opacity, name=name)

    @classmethod
    def create_cylinder(
        cls,
        radius: float,
        length: float,
        pose=None,
        color: list[float] | None = None,
        texture: g.ImageTexture | Path | None = None,
        opacity: float = 1.0,
        name: str | None = None,
    ):
        """Create a cylinder with a given radius and length. The axis of rotational symmetry is aligned with the z-axis
        that is common in robotics. To achieve that, we create a mesh of a cylinder instead of using meshcat cylinder
        that is aligned with y-axis."""
        mesh: trimesh.Trimesh = trimesh.creation.cylinder(radius=radius, height=length, sections=50)
        exp_obj = trimesh.exchange.obj.export_obj(mesh)
        mesh = g.ObjMeshGeometry.from_stream(trimesh.util.wrap_as_stream(exp_obj))
        return cls(mesh, pose=pose, color=color, texture=texture, opacity=opacity, name=name)

    @classmethod
    def create_mesh(
        cls,
        path_to_mesh: str | Path,
        scale: float | list[float] = 1.0,
        pose=None,
        color: list[float] | None = None,
        texture: g.ImageTexture | Path | None = None,
        opacity: float = 1.0,
        name: str | None = None,
    ):
        """Create a mesh object by loading it from the :param path_to_mesh. Loading is performed by 'trimesh' library
        internally."""
        try:
            mesh: trimesh.Trimesh = trimesh.load(path_to_mesh, force='mesh')
        except ValueError as e:
            if str(e) == 'File type: dae not supported':
                print(
                    'To load DAE meshes you need to install pycollada package via '
                    '`conda install -c conda-forge pycollada`'
                    ' or `pip install pycollada`'
                )
            raise
        except Exception as e:
            print(
                f'Loading of a mesh failed with message: \'{e}\'. '
                f'Trying to load with with \'ignore_broken\' but consider to fix the mesh located here:'
                f' \'{path_to_mesh}\'.'
            )
            mesh: trimesh.Trimesh = trimesh.load(path_to_mesh, force='mesh', ignore_broken=True)

        mesh.apply_scale(scale)

        try:  # try to get texture from the mesh
            if hasattr(mesh, 'visual') and hasattr(mesh.visual, 'material') and texture is None:
                n = 100

                def xy_to_uv(xy, w=n, h=n):
                    u = xy[..., 0] / (w - 1)
                    v = 1 - xy[..., 1] / (h - 1)
                    return np.stack((u, v), axis=-1)

                X, Y = np.meshgrid(np.arange(n), np.arange(n))
                uv = xy_to_uv(np.stack((X, Y), axis=-1))
                data = mesh.visual.material.to_color(uv.reshape(-1, 2))
                if data.shape == (4,):
                    data = np.tile(data, n * n).reshape(n, n, 4)
                else:
                    data = data.reshape(n, n, 4)
                b = io.BytesIO()
                Image.fromarray(data).save(b, 'png')
                texture = g.ImageTexture(g.PngImage(b.getvalue()))
        except Exception:
            pass

        try:
            exp_obj = trimesh.exchange.obj.export_obj(mesh)
        except ValueError:
            exp_obj = trimesh.exchange.obj.export_obj(mesh, include_texture=False)

        return cls(
            g.ObjMeshGeometry.from_stream(trimesh.util.wrap_as_stream(exp_obj)),
            pose=pose,
            color=color,
            texture=texture,
            opacity=opacity,
            name=name,
        )


class ArrayWithCallbackOnSetItem(np.ndarray):
    def __new__(cls, input_array, cb=None):
        obj = np.asarray(input_array).view(cls)
        obj.cb = cb
        return obj

    def __setitem__(self, *args, **kwargs):
        super().__setitem__(*args, **kwargs)
        self.cb()

    def __array_finalize__(self, obj, **kwargs):
        if obj is None:
            return
        self.cb = getattr(obj, 'cb', None)

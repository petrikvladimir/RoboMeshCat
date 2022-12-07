#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

import itertools
import time
from pathlib import Path
from tempfile import gettempdir

import imageio
import numpy as np
from PIL import Image
from copy import deepcopy
from typing import Dict, Optional

import meshcat
from meshcat.animation import Animation, AnimationFrameVisualizer

from .object import Object
from .robot import Robot


class Scene:

    def __init__(self, open=True, wait_for_open=True) -> None:
        super().__init__()
        self.objects: Dict[str, Object] = {}
        self.robots: Dict[str, Robot] = {}

        self.camera_pose = np.eye(4)
        self.camera_zoom = 1.

        self.vis = meshcat.Visualizer()
        if open:
            self.vis.open()
        if wait_for_open:
            self.vis.wait()
        self.vis["/Background"].set_property("top_color", [1] * 3)
        self.vis["/Background"].set_property("bottom_color", [1] * 3)

        " Variables used internally in case we are rendering to animation "
        self._animation: Optional[Animation] = None
        self._animation_frame: Optional[AnimationFrameVisualizer] = None
        self._animation_frame_counter: Optional[itertools.count] = None

        " Variables used internally to write frames of the video "
        self._video_writer = None

    def add_object(self, obj: Object, verbose: bool = True):
        if verbose and obj.name in self.objects:
            print('Object with the same name is already inside the scene, it will be replaced. ')
        if verbose and self._animation is not None:
            print('Adding objects while animating is not allowed. You need to add all objects before starting the '
                  'animation.')
            return
        self.objects[obj.name] = obj
        obj._set_vis(self.vis)
        obj._set_object()

    def remove_object(self, obj: Object, verbose: bool = True):
        if verbose and self._animation is not None:
            print('Removing object while animating is not allowed.')
            return
        obj._delete_object()
        self.objects.pop(obj.name)
    #
    # def add_robot(self, robot: Robot, verbose: bool = True):
    #     if verbose and robot.name in self.robots:
    #         print('Robot with the same name is already inside the scene, it will be replaced. ')
    #     self.robots[robot.name] = robot
    #     for obj in robot.objects.values():
    #         self.add_object(obj, verbose=verbose)
    #
    # def remove_robot(self, robot: Robot, verbose: bool = True):
    #     if verbose and self._animation is not None:
    #         print('Removing robots while animating is not allowed.')
    #         return
    #     self.robots.pop(robot.name)
    #     for obj in robot.objects.values():
    #         self.remove_object(obj, verbose=verbose)

    def render(self):
        """Render current scene either to browser, video or to the next frame of the animation. """
        if self._animation is not None:
            self._next_animation_frame()
        else:
            pass
            # self._update_camera(self.vis)
            # self._update_visualization_tree(self.vis)
            # if self._video_writer is not None:
            #     self._video_writer.append_data(np.array(self.render_image()))

    # def _update_camera(self, vis_tree):
    #     vis_tree['/Cameras/default'].set_transform(self.camera_pose)
    #     if np.all(np.isclose(self.camera_pose, np.eye(4))):
    #         self._set_property_animation_safe(vis_tree["/Cameras/default/rotated/<object>"], 'position', [3, 1, 0])
    #     else:
    #         self._set_property_animation_safe(vis_tree["/Cameras/default/rotated/<object>"], 'position', [0, 0, 0])
    #     self._set_property_animation_safe(vis_tree["/Cameras/default/rotated/<object>"], 'zoom', self.camera_zoom)
    #
    # def _set_property_animation_safe(self, element, prop, value, prop_type='number'):
    #     if self._animation is not None:
    #         element.set_property(prop, prop_type, value)
    #     else:
    #         element.set_property(prop, value)
    #
    # def _update_visualization_tree(self, vis_tree):
    #     """Update all poses of the scene in the visualization tree of the meshcat viewer"""
    #     for robot in self.robots.values():
    #         robot.fk()
    #     for o, c in zip(self.objects.values(), self._objects_cache.values()):
    #         vis_tree[o.name].set_transform(o.pose)
    #         if not o.is_material_equal(c) or o.geometry.uuid != c.geometry.uuid:
    #             self.add_object(o, verbose=False)
    #
    # def video_recording(self, filename=None, fps=30, directory=None, **kwargs):
    #     """Return a context manager for video recording.
    #     The output filename is given by:
    #      1) filename parameter if it is not None
    #      2) directory/timestemp.mp4 if filename is None and directory is not None
    #      3) /tmp/timestemp if filename is None and directory is None
    #      """
    #     if filename is None:
    #         if directory is None:
    #             directory = gettempdir()
    #         filename = Path(directory).joinpath(time.strftime("%Y%m%d_%H%M%S.mp4"))
    #     return VideoContext(scene=self, fps=fps, filename=filename, **kwargs)
    #
    # @property
    # def camera_pos(self):
    #     return self.camera_pose[:3, 3]
    #
    # @camera_pos.setter
    # def camera_pos(self, p):
    #     self.camera_pose[:3, 3] = p
    #
    # @property
    # def camera_rot(self):
    #     return self.camera_pose[:3, :3]
    #
    # @camera_rot.setter
    # def camera_rot(self, r):
    #     self.camera_pose[:3, :3] = r
    #
    # def reset_camera(self):
    #     self.camera_pose = np.eye(4)
    #     self.camera_zoom = 1.
    #
    # def render_image(self) -> Image:
    #     return self.vis.get_image()

    def __getitem__(self, item):
        return self.objects[item] if item in self.objects else self.robots[item]

    # def clear(self):
    #     """ Remove all the objects/robots from the scene """
    #     for r in list(self.robots.values()):
    #         self.remove_robot(r)
    #     for o in list(self.objects.values()):
    #         self.remove_object(o)

    """=== The following set of functions handle animations ==="""

    def animation(self, fps: int = 30):
        """ Return context of the animation that allow us to record animations.
            Usage:
                with scene.animation(fps=30):
                    scene['obj'].pos = 3. # set properties of a first frame
                    scene.render() # create a second frame of animation
                    scene['obj'].pos = 3.
         """
        return AnimationContext(scene=self, fps=fps)

    def _next_animation_frame(self):
        """Close the current frame (if exists) and create a new one. Applicable only if animation exists. Set objects
        visualizer to the current frame."""
        assert self._animation is not None
        if self._animation_frame is not None:
            self._animation_frame.__exit__()
        self._animation_frame = self._animation.at_frame(self.vis, next(self._animation_frame_counter))
        self._animation_frame.__enter__()
        "Set all objects visualizers to the frame"
        for o in self.objects.values():
            o._set_vis(self._animation_frame)

    def _close_animation(self):
        """Close the current frame and set objects visualizer to online."""
        assert self._animation is not None
        self._animation_frame.__exit__()
        self._animation_frame = None
        self._animation_frame_counter = None
        self._animation = None
        for o in self.objects.values():
            o._set_vis(self.vis)

    def _start_animation(self, fps):
        """Start animation instead of online changes."""
        self._animation_frame_counter = itertools.count()
        self._animation = Animation(default_framerate=fps)
        self._next_animation_frame()


class AnimationContext:
    """ Used to provide 'with animation' capability for the viewer. """

    def __init__(self, scene: Scene, fps: int) -> None:
        super().__init__()
        self.scene: Scene = scene
        self.fps: int = fps

    def __enter__(self):
        self.scene._start_animation(self.fps)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Publish animation and clear all internal changes that were required to render to frame instead of online """
        self.scene.vis[f'animations/animation'].set_animation(self.scene._animation)
        self.scene._close_animation()


# class VideoContext:
#     def __init__(self, scene: Scene, fps: int, filename: str, **kwargs) -> None:
#         super().__init__()
#         self.scene = scene
#         self.video_writer = imageio.get_writer(uri=filename, fps=fps, **kwargs)
#
#     def __enter__(self):
#         self.scene._video_writer = self.video_writer
#         return self
#
#     def __exit__(self, exc_type, exc_val, exc_tb):
#         self.video_writer.close()
#         self.scene._video_writer = None

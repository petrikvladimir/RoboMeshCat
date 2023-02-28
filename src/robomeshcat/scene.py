#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-10-11
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#
from __future__ import annotations

import itertools
import time
from pathlib import Path
from tempfile import gettempdir

import imageio
import numpy as np
from PIL.Image import Image

import meshcat
from meshcat.animation import Animation, AnimationFrameVisualizer

from .object import Object, ArrayWithCallbackOnSetItem
from .robot import Robot


class Scene:
    def __init__(self, open: bool = True, wait_for_open: bool = True) -> None:
        super().__init__()
        self.objects: dict[str, Object] = {}
        self.robots: dict[str, Robot] = {}

        self.vis = meshcat.Visualizer()
        if open:
            self.vis.open()
        if wait_for_open:
            self.vis.wait()
        self.set_background_color()

        "Variables used to control the camera"
        self._camera_vis = self.vis["/Cameras/default"]
        self._camera_pose = ArrayWithCallbackOnSetItem(np.eye(4), cb=self._set_camera_transform)
        self._camera_pose_modified = False
        self._camera_zoom = 1.0

        " Variables used internally in case we are rendering to animation "
        self._animation: Animation | None = None
        self._animation_frame: AnimationFrameVisualizer | None = None
        self._animation_frame_counter: itertools.count | None = None

        " Variables used internally to write frames of the video "
        self._video_writer = None

    def add_object(self, obj: Object, verbose: bool = True):
        if verbose and obj.name in self.objects:
            print('Object with the same name is already inside the scene, it will be replaced. ')
        if verbose and self._animation is not None:
            print(
                'Adding objects while animating is not allowed.'
                'You need to add all objects before starting the animation.'
            )
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

    def add_robot(self, robot: Robot, verbose: bool = True):
        if verbose and robot.name in self.robots:
            print('Robot with the same name is already inside the scene, it will be replaced. ')
        self.robots[robot.name] = robot
        for obj in robot._objects.values():
            self.add_object(obj, verbose=verbose)

    def remove_robot(self, robot: Robot, verbose: bool = True):
        if verbose and self._animation is not None:
            print('Removing robots while animating is not allowed.')
            return
        self.robots.pop(robot.name)
        for obj in robot._objects.values():
            self.remove_object(obj, verbose=verbose)

    def render(self):
        """Render current scene either to browser, video or to the next frame of the animation."""
        if self._animation is not None:
            self._reset_all_properties()
            self._next_animation_frame()
        if self._video_writer is not None:
            self._video_writer.append_data(np.array(self.render_image()))

    #
    def video_recording(
        self, filename: Path | str | None = None, fps: int = 30, directory: Path | str | None = None, **kwargs
    ):
        """Return a context manager for video recording.
        The output filename is given by:
         1) filename parameter if it is not None
         2) directory/timestemp.mp4 if filename is None and directory is not None
         3) /tmp/timestemp if filename is None and directory is None
        """
        if filename is None:
            if directory is None:
                directory = gettempdir()
            filename = Path(directory).joinpath(time.strftime("%Y%m%d_%H%M%S.mp4"))
        return VideoContext(scene=self, fps=fps, filename=filename, **kwargs)

    def render_image(self) -> Image:
        return self.vis.get_image()

    def __getitem__(self, item):
        return self.objects[item] if item in self.objects else self.robots[item]

    def clear(self):
        """Remove all the objects/robots from the scene"""
        for r in list(self.robots.values()):
            self.remove_robot(r)
        for o in list(self.objects.values()):
            self.remove_object(o)

    def set_background_color(self, top_color=None, bottom_color=None):
        """Set background color of the visualizer. Use white background by default."""
        clr = Object._color_from_input(top_color, default=np.ones(3))
        self.vis["/Background"].set_property("top_color", clr.tolist())
        clr = Object._color_from_input(bottom_color, default=clr)
        self.vis["/Background"].set_property("bottom_color", clr.tolist())

    """=== The following set of functions handle animations ==="""

    def animation(self, fps: int = 30):
        """Return context of the animation that allow us to record animations.
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
        self._camera_vis = self._animation_frame["/Cameras/default"]

    def _close_animation(self):
        """Close the current frame and set objects visualizer to online."""
        assert self._animation is not None
        self._animation_frame.__exit__()
        self._animation_frame = None
        self._animation_frame_counter = None
        self._animation = None
        for o in self.objects.values():
            o._set_vis(self.vis)
        self._camera_vis = self.vis["/Cameras/default"]

    def _start_animation(self, fps):
        """Start animation instead of online changes."""
        self._animation_frame_counter = itertools.count()
        self._animation = Animation(default_framerate=fps)
        self._next_animation_frame()

    def _reset_all_properties(self):
        """Send all the properties to the browser. It is reset for all animation frames to ensure values do not change
        due to the interpolation by the properties set in the future."""
        for o in self.objects.values():
            o._reset_all_properties()
        self.camera_zoom = self._camera_zoom  # this will set the starting value of the property
        if self._camera_pose_modified:
            self.camera_pose = self._camera_pose

    """=== Following functions handle the camera control ==="""

    @property
    def camera_zoom(self):
        return self._camera_zoom

    @camera_zoom.setter
    def camera_zoom(self, v):
        self._camera_zoom = v
        self._set_property(self._camera_vis['rotated/<object>'], 'zoom', self._camera_zoom, 'number')

    @property
    def camera_pose(self):
        return self._camera_pose

    @camera_pose.setter
    def camera_pose(self, v):
        self._camera_pose[:, :] = v

    @property
    def camera_pos(self):
        return self._camera_pose[:3, 3]

    @camera_pos.setter
    def camera_pos(self, p):
        self._camera_pose[:3, 3] = p

    @property
    def camera_rot(self):
        return self._camera_pose[:3, :3]

    @camera_rot.setter
    def camera_rot(self, r):
        self._camera_pose[:3, :3] = r

    def reset_camera(self):
        """Reset camera to default pose and let user interact with it again."""
        self._camera_pose = ArrayWithCallbackOnSetItem(np.eye(4), cb=self._set_camera_transform)
        self._camera_vis.set_transform(self._camera_pose)
        self.camera_zoom = 1.0
        self._camera_enable_user_control()
        self._camera_pose_modified = False

    def _set_camera_transform(self):
        # disable human interaction if camera pose is set
        self._camera_vis.set_transform(self._camera_pose)
        self._camera_disable_user_control()
        self._camera_pose_modified = True

    def _camera_disable_user_control(self):
        self._set_property(self._camera_vis['rotated/<object>'], 'position', [0, 0, 0], 'vector')

    def _camera_enable_user_control(self):
        self._set_property(self._camera_vis['rotated/<object>'], 'position', [3, 1, 0], 'vector')

    @staticmethod
    def _set_property(element, key, value, prop_type='number'):
        """Set property of the object, handle animation frames set_property internally."""
        if isinstance(element, AnimationFrameVisualizer):
            element.set_property(key, prop_type, value)
        else:
            element.set_property(key, value)


class AnimationContext:
    """Used to provide 'with animation' capability for the viewer."""

    def __init__(self, scene: Scene, fps: int) -> None:
        super().__init__()
        self.scene: Scene = scene
        self.fps: int = fps

    def __enter__(self):
        self.scene._start_animation(self.fps)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Publish animation and clear all internal changes that were required to render to frame instead of online"""
        self.remove_clips_duplicates()
        self.scene.vis['animations/animation'].set_animation(self.scene._animation)
        self.scene._close_animation()

    def remove_clips_duplicates(self):
        """Meshcat doesn't like if same property as modified twice in the same frame - it does weird jumping in
        animation. In this function we find such a duplicates and keep only the last change of the property."""
        for clip in self.scene._animation.clips.values():
            for track in clip.tracks.values():
                indices_to_remove = set()
                last_f = None
                for i, f in enumerate(track.frames):
                    if f == last_f:
                        indices_to_remove.add(i - 1)
                    last_f = f
                if len(indices_to_remove) > 0:
                    track.frames = [f for i, f in enumerate(track.frames) if i not in indices_to_remove]
                    track.values = [v for i, v in enumerate(track.values) if i not in indices_to_remove]


class VideoContext:
    def __init__(self, scene: Scene, fps: int, filename: str | Path, **kwargs) -> None:
        super().__init__()
        self.scene = scene
        self.video_writer = imageio.get_writer(uri=filename, fps=fps, **kwargs)

    def __enter__(self):
        self.scene._video_writer = self.video_writer
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.video_writer.close()
        self.scene._video_writer = None

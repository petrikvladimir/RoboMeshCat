#!/usr/bin/env python
#
# Copyright (c) CTU -- All Rights Reserved
# Created on: 2022-11-10
#     Author: Vladimir Petrik <vladimir.petrik@cvut.cz>
#

from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

from robomeshcat import Object, Scene

example_folder = Path(__file__).parent

"All elements are stored in Scene that is responsible for rendering them in the MeshCat"
scene = Scene()

"You can objects into the scene and refer to them through the object instance or by the name"
obj1 = Object.create_sphere(radius=0.1, name='red_sphere', opacity=0.5, color=[1., 0., 0.])
scene.add_object(obj1)

scene.render()
input('Rotate the scene as you wish and press enter to capture the image.')

"Render the image via matplotlib"
img = scene.render_image()

fig, ax = plt.subplots(1, 1, squeeze=True)  # type: plt.Figure, plt.Axes
ax.imshow(img)
plt.show()

"Store the video"
with scene.video_recording(filename='/tmp/video.mp4', fps=30):
    for t in np.linspace(1, 0, 30):
        obj1.pos[2] = t
        scene.render()

    t = np.linspace(0, 2 * np.pi, 60)
    for tt in t:
        scene.camera_pos[0] = np.sin(tt)
        scene.camera_pos[1] = np.cos(tt)
        scene.camera_pos[2] = 1
        scene.render()

scene.reset_camera()
scene.render()

# RoboMeshCat
[![](https://anaconda.org/conda-forge/robomeshcat/badges/version.svg)](https://anaconda.org/conda-forge/robomeshcat)
[![PyPI version](https://badge.fury.io/py/robomeshcat.svg)](https://badge.fury.io/py/robomeshcat)
![](https://anaconda.org/conda-forge/robomeshcat/badges/downloads.svg)
[![License](https://img.shields.io/badge/License-BSD_2--Clause-orange.svg)](https://opensource.org/licenses/BSD-2-Clause)

Set of utilities for visualizing robots in web-based visualizer [MeshCat](https://github.com/rdeits/meshcat-python).
The whole library is object and robot centric allowing you to modify properties of instances rather than manipulating
the visualization tree of the MeshCat itself.
The library allows you to easily generate videos like this (source code is [here](examples/05_teaser.py)):

![](https://raw.githubusercontent.com/petrikvladimir/robomeshcat/main/docs/output.gif)

# Installation

## From <img src="https://s3.amazonaws.com/conda-dev/conda_logo.svg" height="18">

```bash
conda install -c conda-forge robomeshcat
```

## From PyPI

```bash
pip install robomeshcat
```

# Features

## Object and robot centric rendering

- supported objects shapes are sphere, cuboid, cylinder, and mesh; you can control:
    - color
    - transparency/opacity
    - pose
- robots can be loaded from URDF (internally represented by [pinocchio](https://github.com/stack-of-tasks/pinocchio)
  library) and you can control:
    - color
    - transparency/opacity
    - pose of the base
    - configuration, i.e. joint values

```python
from robomeshcat import Object, Robot, Scene
from example_robot_data.robots_loader import PandaLoader
from pathlib import Path

"Create a scene that stores all objects and robots and has rendering capability"
scene = Scene()
obj = Object.create_sphere(radius=0.1, name='red_sphere', opacity=0.5, color=[1., 0., 0.])
scene.add_object(obj)
robot = Robot(urdf_path=PandaLoader().df_path, mesh_folder_path=Path(PandaLoader().model_path).parent.parent)
scene.add_robot(robot)
"Render the initial scene"
scene.render()
"Update object position in x-axis and robot first joint"
obj.pos[0] = 1.  # or scene['red_sphere'].pos[0] = 1.
robot[0] = 3.14
scene.render()
```

## Animation rendering

- you can easily animate properties:
    - poses of the objects
    - configurations and poses of robots
    - camera pose and zoom
- animation is published automatically after 'with' command finishes/closes

```python
from robomeshcat import Scene

scene = Scene()
with scene.animation(fps=30):
    scene.render()  # generate first frame
    scene.camera_zoom = 0.4  # set the camera zoom, you can also set position and rotation of camera
    scene['obj'].pos[1] = 1.  # move hte object in the second frame
    scene.render()  # generate second frame
```

## Image generation

```python
from robomeshcat import Scene

scene = Scene()
img = scene.render_image()
```

## Video recording

```python
from robomeshcat import Scene

scene = Scene()
with scene.video_recording(filename='/tmp/video.mp4', fps=30):
    pass
```

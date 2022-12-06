# Visualizing human model in meshcat via SMPL-X

## Installation

The SMPL-X library and model data are not included in a standard RoboMeshCat packages.
It must be installed as described in [SMPL-X package](https://github.com/vchoutas/smplx), i.e. by running

```bash
pip install smplx[all]
```

and then downloading the data from [here](https://smpl-x.is.tue.mpg.de/).

## Usage
To create an animation we need to know all shapes before animation starts as it relies on mesh morphologies in meshcat.

```bash
export SMPLX_MODEL_PATH=<fill in the path>
```
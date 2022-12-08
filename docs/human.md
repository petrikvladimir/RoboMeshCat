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

```python
human = Human(pose=human_default_pose, color=[1., 0., 0.], model_path=smplx_models_path)
scene.add_object(human)  # add human to the scene, it will be visualized immediately

human.update_vertices(vertices=human.get_vertices(expression=torch.randn([1, 10])))

human.smplx_model.body_pose.data += 0.1
human.update_vertices()
```

## Coloring of human
You have two options to color the human mesh: (i) uniform color and (ii) per vertex color.
Uniform color is default, it can be set with `color` argument of human and changed/animated by `.color` property.

Per vertex color is cannot be animated as it requires to change the geometry internally. 
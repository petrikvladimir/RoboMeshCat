# Visualizing human model in meshcat via SMPL-X

## Installation

The SMPL-X library and model data are not included in a standard RoboMeshCat packages.
It must be installed as described in [SMPL-X package](https://github.com/vchoutas/smplx), i.e. by running

```bash
pip install smplx[all]
```

and then downloading the data from [here](https://smpl-x.is.tue.mpg.de/), we use SMPL-X v1_1 data from the webpage.
The path to the model must be specified while creating the instance of the Human.
In the examples, the following folder structure is assumed:

```bash
examples/
  models/  # this is a folder downloaded from the webpage above
    smplx/
      SMPLX_FEMALE.npz
      SMPLX_FEMALE.pkl
      SMPLX_MALE.npz
      ...
  06_human.py # this is an example script
```

## Usage

The human model functionality is available through the class `Human`.
You can change human pose (i.e. position and orientation), color, visibility, etc. in the same way as for regular
RoboMeshCat objects, and you can also change the body pose (i.e. configuration), shape and expression through the 
instance of the class.
For complete example have a look at [06_human.py](../examples/06_human.py).

### Online usage

```python
human = Human(pose=human_default_pose, color=[1., 0., 0.], model_path=smplx_models_path)
scene.add_object(human)  # add human to the scene, it will be visualized immediately

human.update_vertices(vertices=human.get_vertices(expression=torch.randn([1, 10])))

human.smplx_model.body_pose.data += 0.1
human.update_vertices()
```

### Animation

Function `update_vertices` cannot be used in animation as it is modifying geometry of the object internally.
Instead, you need to use 'morphologies', that need to be specified before adding human to the scene:

```python
human = Human(pose=human_default_pose, color=[1., 0., 0.], model_path=smplx_models_path)
human.smplx_model.betas.data += 1
human.add_morph(human.get_vertices())  # the first morph changes the shape

human.smplx_model.body_pose.data += 0.1
human.add_morph(human.get_vertices())  # the second morp changes the body pose

scene.add_object(human)  # add human to the scene, no morphology can be added/modified after this step

"Let's animate"
with scene.animation(fps=1):
    human.display_morph(None)  # this will display the human shape that is not affected by morphologies
    scene.render()

    human.display_morph(0)
    scene.render()

    human.display_morph(1)
    scene.render()
```

### Coloring of human

You have two options to color the human mesh: (i) uniform color and (ii) per vertex color.
Uniform color is default, it can be set with `color` argument of human and changed/animated by `.color` property.

Per vertex color cannot be animated as it requires to change the geometry internally. 
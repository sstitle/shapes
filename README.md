# shapes

Nix environment for working with shapes.

Install Nix with the Determinate Systems installer [here](https://github.com/DeterminateSystems/nix-installer):

```bash
curl --proto '=https' --tlsv1.2 -sSf -L https://install.determinate.systems/nix | \
  sh -s -- install
```

## Line Intersection Visualizer

Simple demonstration application showing the calculation of the point of intersection of two line segments.

![Screenshot](screenshot.png)

```bash
nix run
```

## Development environment 

Development environment is provided using Nix and UV.

To enter the development environment run:

```bash
nix develop
```

And to run the script:

```bash
uv run main.py
```



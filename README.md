# skd1_docs

Documentation and first-time setup guides for **SKD-1**, our experimental 4WD skid-steer
robot running ROS 2 Jazzy on Ubuntu 24.04 with Gazebo Harmonic.

The guides walk through the same path as the Nav2
[First-Time Robot Setup Guide](https://docs.nav2.org/setup_guides/index.html)
(transforms, URDF, simulation, odometry, sensors, SLAM, footprint, planner and controller
selection), but every step is explained with the real SKD-1 files instead of the generic
`sam_bot` example.

Start here: **[docs/setup_guides/index.md](docs/setup_guides/index.md)**

Published site (GitHub Pages): `https://<github-user>.github.io/<repo-name>/`
(for example `https://gmsanchez.github.io/skd1_docs/`).

## Related repositories

| Repository | Content |
|---|---|
| [skd1](https://github.com/gmsanchez/skd1) | Base packages: description, control, hardware interface, localization, navigation, teleop, bringup |
| [skd1_sensors](https://github.com/gmsanchez/skd1_sensors) | RPLidar C1, Phidgets Spatial IMU and u-blox F9P bringup |
| [skd1_simulation](https://github.com/gmsanchez/skd1_simulation) | Gazebo worlds and launch files |
| [skd1_visualization](https://github.com/gmsanchez/skd1_visualization) | RViz configs and launch files |
| [skd1_extra](https://github.com/gmsanchez/skd1_extra) | Design files and BoM |
| [hibachi_firmware](https://github.com/gmsanchez/hibachi_firmware) | STM32 low level motor controller firmware |

`skd1.repos` imports the ROS packages into a workspace with `vcs import`.

## Attribution

These guides are adapted from the Nav2 documentation and tutorials
([navigation2](https://github.com/ros-navigation/navigation2),
[navigation2_tutorials](https://github.com/ros-navigation/navigation2_tutorials)) through
[sam_bot_jazzy](https://github.com/gmsanchez/sam_bot_jazzy), all under the Apache 2.0 license.
The conceptual text and the four sensor-message images are reused; the examples,
commands and configuration are specific to SKD-1. See [MIGRATION.md](MIGRATION.md) for what changed.

## Building the documentation

The documentation is written in Markdown and built with [Sphinx](https://www.sphinx-doc.org/)
([MyST](https://myst-parser.readthedocs.io/) for Markdown, [Furo](https://pradyunsg.me/furo/) theme).

``` shell
python3 -m venv .venv && source .venv/bin/activate
pip install -r docs/requirements.txt
sphinx-build -W -b html docs docs/_build/html
python3 -m http.server -d docs/_build/html 8000   # then open http://localhost:8000
```

`-W` turns warnings (such as broken cross-references) into errors, which is how CI builds it.

### Writing conventions

-   Callouts use GitHub alert syntax, which renders on GitHub and in the site:
    `> [!NOTE]`, `> [!WARNING]` or `> [!IMPORTANT]` followed by the text on `> ` lines.
-   Diagrams use ```` ```mermaid ```` fences.
-   A new page must be added to the `toctree` in `docs/index.md`, or the build will warn about it.

### Publishing

`.github/workflows/docs.yml` builds the site on every push and pull request, and deploys it to GitHub
Pages on pushes to `main`. One-time setup: in the repository go to **Settings → Pages** and set
**Source** to **GitHub Actions**.

# SKD-1 documentation

Documentation for **SKD-1**, our experimental 4WD skid-steer robot running ROS 2 Jazzy on
Ubuntu 24.04 with Gazebo Harmonic.

The [first-time setup guides](setup_guides/index.md) follow the structure of the Nav2
[First-Time Robot Setup Guide](https://docs.nav2.org/setup_guides/index.html), but every step is
explained with the real SKD-1 packages, in simulation and on the robot.

## Related repositories

| Repository | Content |
|---|---|
| [skd1](https://github.com/gmsanchez/skd1) | Base packages: description, control, hardware interface, localization, navigation, teleop, bringup |
| [skd1_sensors](https://github.com/gmsanchez/skd1_sensors) | RPLidar C1, Phidgets Spatial IMU and u-blox F9P bringup |
| [skd1_simulation](https://github.com/gmsanchez/skd1_simulation) | Gazebo worlds and launch files |
| [skd1_visualization](https://github.com/gmsanchez/skd1_visualization) | RViz configs and launch files |
| [skd1_extra](https://github.com/gmsanchez/skd1_extra) | Design files and BoM |
| [hibachi_firmware](https://github.com/gmsanchez/hibachi_firmware) | STM32 low level motor controller firmware |

```{toctree}
:maxdepth: 1
:caption: Setup guides

setup_guides/index
setup_guides/workspace/setup_workspace
setup_guides/transformation/setup_transforms
setup_guides/urdf/setup_urdf
setup_guides/simulation/setup_gazebo
setup_guides/odom/setup_odom
setup_guides/odom/setup_robot_localization
setup_guides/sensors/setup_sensors
setup_guides/sensors/mapping_localization
setup_guides/footprint/setup_footprint
setup_guides/algorithm/select_algorithm
```

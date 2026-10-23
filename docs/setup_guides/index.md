# First-Time Robot Setup Guide for SKD-1

This section is a collection of guides that explain how SKD-1 is set up to run Nav2, on both
the real robot and in Gazebo simulation. They follow the structure of the Nav2 setup guides,
but use the actual SKD-1 packages.

The guides are meant to:

-   Document why each SKD-1 file and parameter exists
-   Help a new team member reproduce the setup, in simulation first and then on hardware
-   Act as a checklist when modifying the robot (new sensor, new wheels, new payload)
-   Point to the right repository and file for every topic

SKD-1 is a four wheel skid-steer vehicle, so some topics differ from a standard differential
drive robot (wheel separation multiplier, planner and controller choice). Those differences
are called out in each guide.

> [!NOTE]
> **Versions:** Ubuntu 24.04, ROS 2 Jazzy Jalisco, Gazebo Harmonic.
> The Gazebo Classic variants of the original Nav2 guides are intentionally not carried over.

## Table of Contents

0. [Workspace and Prerequisites](workspace/setup_workspace.md)
1. [Setting Up Transformations](transformation/setup_transforms.md)
2. [Setting Up The URDF](urdf/setup_urdf.md)
3. [Setting Up The Robot in Gazebo](simulation/setup_gazebo.md)
4. [Setting Up Odometry](odom/setup_odom.md)
5. [Fusing Odometry with Robot Localization](odom/setup_robot_localization.md)
6. [Setting Up Sensors](sensors/setup_sensors.md)
7. [Mapping and Localization](sensors/mapping_localization.md)
8. [Setting Up the Robot's Footprint](footprint/setup_footprint.md) (Optional)
9. [Setting Up Navigation Plugins](algorithm/select_algorithm.md) (Optional)

> [!NOTE]
> These guides are not full tuning guides. For detailed discussions on how to
> customize and tune Nav2, see the [Nav2 docs](https://docs.nav2.org/index.html).

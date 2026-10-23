# Workspace and Prerequisites

This guide is new compared to the Nav2 setup guides. SKD-1 is split across several
repositories, so before anything else you need a workspace that contains all of them.

## Where each guide's files live

| Topic | Package | Repository |
|---|---|---|
| URDF, meshes, robot state publisher | `skd1_description` | skd1 |
| Wheel controller (`diff_drive_controller`) | `skd1_control` | skd1 |
| ros2_control hardware plugin (serial link to the STM32) | `skd_base` | skd1 |
| EKF and GPS fusion | `skd1_localization` | skd1 |
| SLAM and Nav2 configuration | `skd1_navigation` | skd1 |
| Joystick and velocity multiplexer | `skd1_teleop` | skd1 |
| Launch files for the real robot | `skd1_bringup` | skd1 |
| RPLidar C1, Phidgets IMU, u-blox F9P | `rplidar_c1_bringup`, `phidgets_spatial_bringup`, `f9p_ublox` | skd1_sensors |
| Gazebo worlds and launch files | `skd1_gz` | skd1_simulation |
| RViz configs | `skd1_rviz` | skd1_visualization |
| Low level firmware | `hibachi_firmware` (PlatformIO) | hibachi_firmware |

## Simulation or hardware

SKD-1 uses one URDF for both cases. The xacro argument `is_sim` selects the
`ros2_control` plugin and whether the Gazebo sensor blocks are included
(see [Setting Up The URDF](../urdf/setup_urdf.md)). In launch files this is driven by
`use_sim_time`.

| | Simulation | Real robot |
|---|---|---|
| Clock | Gazebo (`use_sim_time:=true`) | System clock |
| Wheel interface | `gz_ros2_control/GazeboSimSystem` | `skd_base/SKDHardware` over serial |
| Sensors | Gazebo sensors bridged with `ros_gz_bridge` | Real drivers from skd1_sensors |
| Entry point | `skd1_gz` launch files | `skd1_bringup` launch files |

## Install dependencies

Install ROS 2 Jazzy following the
[official instructions](https://docs.ros.org/en/jazzy/Installation.html), then:

``` shell
sudo apt install \
  ros-dev-tools python3-vcstool \
  ros-jazzy-xacro ros-jazzy-joint-state-publisher-gui ros-jazzy-rviz2 \
  ros-jazzy-ros2-control ros-jazzy-ros2-controllers \
  ros-jazzy-robot-localization ros-jazzy-slam-toolbox \
  ros-jazzy-navigation2 ros-jazzy-nav2-bringup \
  ros-jazzy-twist-mux ros-jazzy-teleop-twist-joy ros-jazzy-teleop-twist-keyboard
```

For simulation add:

``` shell
sudo apt install ros-jazzy-ros-gz ros-jazzy-gz-ros2-control
```

For the real robot's sensors add (check each name with `apt-cache policy`; if a driver is
not available as a binary, build it from source in the same workspace):

``` shell
sudo apt install ros-jazzy-phidgets-spatial ros-jazzy-imu-filter-madgwick ros-jazzy-laser-filters
# sllidar_ros2: https://github.com/Slamtec/sllidar_ros2
# ublox (needed by f9p_ublox): see skd1_sensors/f9p_ublox/package.xml
```

> [!NOTE]
> The `package.xml` files of `skd1_localization` and `skd1_navigation` do not
> declare their runtime dependencies (`robot_localization`, `slam_toolbox`, `nav2_*`), so
> `rosdep` will not install them. Install them manually as shown above.

## Create and build the workspace

``` shell
mkdir -p ~/workspaces/skd1_ros2_ws/src
cd ~/workspaces/skd1_ros2_ws/src
vcs import < /path/to/skd1_docs/skd1.repos
cd ..
rosdep install --from-paths src --ignore-src -r -y
colcon build --symlink-install
source install/setup.bash
```

On a machine used only for simulation, skip the real-hardware sensor packages if their
drivers are not installed:

``` shell
colcon build --symlink-install --packages-skip rplidar_c1_bringup phidgets_spatial_bringup f9p_ublox
```

Check that the packages are visible:

``` shell
ros2 pkg list | grep -E "skd|rplidar|phidgets|f9p"
```

## Environment for the real robot

`skd1/skd1_configure_ros2_environment.sh` sets up the robot's environment: it sources ROS and the
workspace, sets `ROS_DOMAIN_ID=42`, selects `rmw_fastrtps_cpp`, and points
`ROS_DISCOVERY_SERVER` to `192.168.1.100:42100`. The companion script
`skd1_launch_fastdds_server.sh` starts the Fast DDS discovery server on that address.
Both scripts contain absolute paths and IP addresses specific to our network
(`/home/ubuntu/workspaces/skd1_ros2_ws`, `192.168.1.100`), so adjust them to your setup.

You do not need either script for simulation.

## Smoke test

``` shell
ros2 launch skd1_gz skd1_gz_launch.py
```

Gazebo opens an empty world with SKD-1. In another terminal:

``` shell
ros2 topic list | grep -E "scan|imu|odom|joint_states"
```

You are now ready for the [next guide](../transformation/setup_transforms.md).

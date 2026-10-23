# Setting Up The Robot in Gazebo

This guide replaces the "Setting Up The SDF - Gazebo" guide of the original Nav2 series.
There, a second description file (SDF) was written by hand and the sensors and plugins were added
to it. SKD-1 takes the other route documented in the Nav2 guides: **the URDF stays the single source
of truth** and Gazebo-specific parts are added with `<gazebo>` extension tags. The robot is spawned
in Gazebo directly from the `/robot_description` topic, so there is no SDF to maintain.

Simulation files live in the [skd1_simulation](https://github.com/gmsanchez/skd1_simulation)
repository (package `skd1_gz`) and in `skd1_description`.

## What Gazebo Needs

The Gazebo simulation of a ROS robot needs five things. For each one this table shows where it is on SKD-1:

| Need | Where |
|---|---|
| A world | `skd1_gz/worlds/*.world` |
| The robot model, with collisions and inertia | `skd1_description` (same URDF as the real robot) |
| Simulated sensors | `skd1_description/urdf/skd1_sim_sensors.urdf.xacro` |
| Simulated actuators and odometry | `skd1_description/urdf/skd1_sim_ros2_control.urdf.xacro` |
| A bridge between Gazebo and ROS topics | `ros_gz_bridge` node in `skd1_gz/launch/skd1_gz_launch.py` |

## Worlds

| World | Launch file | Spawn pose (x, y, z, yaw) |
|---|---|---|
| Empty | `skd1_gz_launch.py` | 0, 0, 0.17, 0 |
| TurtleBot3 world | `skd1_gz_turtlebot3_world_launch.py` | 0, -3.5, 0.09, π/2 |
| Small warehouse (AWS RoboMaker models) | `skd1_gz_small_warehouse_world_launch.py` | 0, -2.0, 0.13, π/2 |

The models used by the worlds are in `skd1_gz/models`. The launch file appends that folder to
`GZ_SIM_RESOURCE_PATH` so that Gazebo can find them. To use your own world, pass it with the
`world_path` argument and adjust `x`, `y`, `z` and `yaw`:

``` shell
ros2 launch skd1_gz skd1_gz_launch.py world_path:=/path/to/my.world x:=1.0 y:=0.0 z:=0.17 yaw:=0.0
```

## Simulated Sensors

`skd1_sim_sensors.urdf.xacro` attaches Gazebo sensors to the URDF links, using `<gazebo reference="...">`
blocks. They are included only when `is_sim` is true. They mirror the real sensors, using
**the same topic names and frames**, so the rest of the stack does not know whether it runs on
the robot or in simulation:

| Sensor | Link | Gazebo type | Topic | Rate |
|---|---|---|---|---|
| Phidgets IMU | `phidgets_imu_link` | `imu` (with noise) | `phidgets_373223/imu/data` | 20 Hz |
| Phidgets magnetometer | `phidgets_imu_link` | `magnetometer` | `phidgets_373223/imu/mag` | 20 Hz |
| RPLidar C1 | `rplidar_link` | `gpu_lidar` (360 samples, 0.25 to 12 m, 0.01 m noise) | `scan` | 10 Hz |
| ArduSimple GPS | `ardusimple_gps_link` | `navsat` (no noise) | `ardusimple/fix` | 1 Hz |

## Simulated Actuators and Odometry

`skd1_sim_ros2_control.urdf.xacro` does three things:

-   Declares a `ros2_control` system that uses the `gz_ros2_control/GazeboSimSystem` plugin and
    exposes a velocity command interface and position and velocity state interfaces for each of the
    four wheel joints. On the real robot the same joints are exposed by `skd_base/SKDHardware`.
-   Loads `gz_ros2_control` with the controller configuration `skd1_control/config/diff_drive_controller.yaml`.
    This is the **same file** used on the real robot.
-   Adds the Gazebo `OdometryPublisher` plugin that publishes the **ground truth** pose on
    `/ground_truth/odometry`, `/ground_truth/odometry_with_covariance` and `/ground_truth/pose`.
    This is not used by Nav2; it is useful to evaluate how good the estimated odometry is.

## The Launch File

`skd1_gz/launch/skd1_gz_launch.py` performs the following steps, in order:

1.  Appends `skd1_gz/models` to `GZ_SIM_RESOURCE_PATH`.
2.  Starts Gazebo with `ros_gz_sim` (`gz_args: -r -v 4 <world>`).
3.  Starts the `ros_gz_bridge` `parameter_bridge`.
4.  Starts the `robot_state_publisher` through `skd1_description_launch.py`.
5.  Spawns the robot with `ros_gz_sim create -topic robot_description` at the pose given by `x`, `y`, `z`, `yaw`.
6.  Spawns the `joint_state_broadcaster` and then, when it finishes, the `skd1_base_controller`
    (an `OnProcessExit` event handler enforces the order).

### The bridge

Topics in Gazebo and in ROS 2 are different systems. The `parameter_bridge` arguments have the
form `topic@ros_type<gz_type`, where the symbol after the ROS type sets the direction: `[` is
Gazebo to ROS, `]` is ROS to Gazebo and `@` is bidirectional. SKD-1 bridges these topics, all from Gazebo to ROS:

| Topic | ROS type |
|---|---|
| `/clock` | `rosgraph_msgs/msg/Clock` |
| `/ardusimple/fix` | `sensor_msgs/msg/NavSatFix` |
| `/phidgets_373223/imu/data` | `sensor_msgs/msg/Imu` |
| `/phidgets_373223/imu/mag` | `sensor_msgs/msg/MagneticField` |
| `/scan` | `sensor_msgs/msg/LaserScan` |
| `/scan/points` | `sensor_msgs/msg/PointCloud2` |
| `/ground_truth/odometry`, `/ground_truth/odometry_with_covariance`, `/ground_truth/pose` | `nav_msgs/msg/Odometry`, `geometry_msgs/msg/PoseArray` |

Notice there is no bridge for `/cmd_vel`, `/odom`, `/tf` or `/joint_states`. The wheel commands
and joint states flow through `ros2_control` (`gz_ros2_control`) instead, and odometry and
`odom` => `base_link` are computed by the controller and the EKF, exactly as on the real
robot. This differs from the Nav2 sample robot, which used the Gazebo `DiffDrive` plugin and bridged those topics.

## Build, Run and Verification

``` shell
cd ~/workspaces/skd1_ros2_ws
colcon build --symlink-install
source install/setup.bash
ros2 launch skd1_gz skd1_gz_turtlebot3_world_launch.py
```

Gazebo opens with SKD-1 in the TurtleBot3 world. Check that the controllers are active:

``` shell
ros2 control list_controllers
```

You should see `joint_state_broadcaster` and `skd1_base_controller` as `active`. Check the topics:

``` shell
ros2 topic list
```

and make sure `/scan`, `/phidgets_373223/imu/data`, `/joint_states` and `/skd1_base_controller/odom` are present.

Drive the robot from the keyboard. `twist_mux` is not running with this launch file, so publish
directly to the controller (it takes `TwistStamped` messages):

``` shell
ros2 run teleop_twist_keyboard teleop_twist_keyboard --ros-args -p stamped:=true --remap cmd_vel:=/skd1_base_controller/cmd_vel
```

<!-- TODO(screenshot): SKD-1 in the TurtleBot3 world in Gazebo -->

> [!NOTE]
> `diff_drive_controller` has `use_stamped_vel: true`, so it expects `geometry_msgs/TwistStamped`.
> Nav2 nodes are configured with `enable_stamped_cmd_vel: True` for the same reason.
> `teleop_twist_keyboard` must be started with `stamped:=true`.

## Conclusion

SKD-1 is simulated from the same URDF as the real robot. Gazebo-specific parts are kept in
separate Xacro files that are only included when `is_sim` is true, and the simulated sensors publish
on the same topics as the real drivers. In the next guide we look at the controller and odometry system that
runs both in simulation and on hardware.

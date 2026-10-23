# Mapping and Localization

Now that SKD-1 has its sensors, we use the laser scan to build a map of the environment and to
localize the robot in it. The `slam_toolbox` package provides 2D Simultaneous Localization and
Mapping (SLAM) and is one of the officially supported SLAM libraries of Nav2. Localization on
an existing map can also be done with `nav2_amcl`, which implements Adaptive Monte Carlo
Localization. Both use a `sensor_msgs/LaserScan`, which on SKD-1 is published on `/scan`.

> [!NOTE]
> **See also:**
> The [slam_toolbox repository](https://github.com/SteveMacenski/slam_toolbox#readme) lists all its parameters, the
> [AMCL Configuration Guide](https://docs.nav2.org/configuration/packages/configuring-amcl.html)
> covers AMCL, and
> [Navigating While Mapping](https://docs.nav2.org/tutorials/docs/navigation2_with_slam.html) shows how Nav2 is used with SLAM.

All the configuration of this guide is in
`skd1_navigation/config` of the [skd1](https://github.com/gmsanchez/skd1) repository.

## Costmap 2D

The costmap package uses sensor information to build an occupancy grid whose cells hold a cost
between 0 (free) and 254 (lethal obstacle). Values in between steer the robot away from
obstacles as a potential field. Costmaps in Nav2 are implemented by `nav2_costmap_2d`, which is
made of plugin layers:

-   **Static layer:** the map published on `/map` (for example by SLAM).
-   **Obstacle layer:** obstacles detected by `LaserScan` or `PointCloud2` sources.
-   **Voxel layer:** like the obstacle layer, but handling 3D data.
-   **Range layer:** sonar and infrared sensors.
-   **Inflation layer:** adds cost around lethal obstacles to account for the robot's size.

Nav2 uses two costmaps: the **global costmap** for long-term planning over the whole map, and
the **local costmap** for short-term planning and collision avoidance.

### SKD-1 Costmap Configuration

Both are defined in `nav2_params.yaml`. The key differences between them:

| | Local costmap | Global costmap |
|---|---|---|
| `global_frame` | `odom` | `map` |
| Window | Rolling, 5 × 5 m | Whole map (`track_unknown_space: true`) |
| `update_frequency` / `publish_frequency` | 5 Hz / 2 Hz | 1 Hz / 1 Hz |
| Plugins | `voxel_layer`, `inflation_layer` | `static_layer`, `obstacle_layer`, `inflation_layer` |
| Inflation | `inflation_radius: 0.8`, `cost_scaling_factor: 0.5` | `inflation_radius: 0.4`, `cost_scaling_factor: 1.0` |
| Scan range limits | min 0.20 m, obstacle max 2.5 m, raytrace max 12 m | min 0.30 m, obstacle max 2.5 m, raytrace max 12 m |
| Footprint | Polygon (see [Setting Up the Robot's Footprint](../footprint/setup_footprint.md)) | Same polygon |

Both costmaps use the `/scan` topic with `data_type: "LaserScan"`, `clearing: True` and
`marking: True`, and set `inf_is_valid: true`. That last parameter matches the range filter of
the real lidar, which replaces out-of-range readings with `inf` (see
[Setting Up Sensors](setup_sensors.md)).

The minimum ranges are larger than zero to avoid the robot detecting its own body, and
the maximum obstacle range of 2.5 m keeps the costmaps focused on nearby obstacles while the
raytracing range of 12 m is the range of the lidar, so that far free space is still cleared.

## Configuring slam_toolbox

SKD-1 uses the asynchronous online mode of `slam_toolbox`, with the configuration in
`skd1_navigation/config/mapper_params_online_async.yaml`. This file is a copy of the one that
comes with `slam_toolbox`, with the changes below, which are the ones that matter for SKD-1:

| Parameter | SKD-1 value | Why |
|---|---|---|
| `odom_frame`, `map_frame`, `base_frame` | `odom`, `map`, `base_footprint` | Frames used by SLAM. Note `base_footprint`. |
| `scan_topic` | `/scan` | Filtered scan. |
| `mode` | `mapping` | Switch to `localization` to localize on a saved map. |
| `transform_publish_period` | `0.0` | **Disables the `map` => `odom` broadcast.** The global EKF publishes it instead. |
| `min_laser_range`, `max_laser_range` | 0.25, 12.0 | Matches the RPLidar C1. |
| `minimum_travel_distance`, `minimum_travel_heading` | 0.25, 0.25 | SKD-1 is small and slow, so scans are processed more often than in the default (0.5). |
| `restamp_tf` | `false` | |
| `use_map_saver` | `true` | Enables saving maps from the `slam_toolbox` map saver. |

> [!IMPORTANT]
> Only one node can publish `map` => `odom`. The default `slam_toolbox` configuration publishes it
> (`transform_publish_period: 0.02`). On SKD-1 it is disabled on purpose, and the pose that SLAM
> publishes on `/pose` is fused by the global EKF
> (see [Fusing Odometry with Robot Localization](../odom/setup_robot_localization.md)).
> If you restore the default you must also stop the global EKF's TF broadcast.

## Launching the Stack

### Simulation

``` shell
# Terminal 1: Gazebo and the robot
ros2 launch skd1_gz skd1_gz_turtlebot3_world_launch.py

# Terminal 2: teleop, local and global EKF, slam_toolbox and Nav2
ros2 launch skd1_gz skd1_gz_nav2_launch.py

# Terminal 3: RViz
ros2 launch skd1_rviz skd1_rviz_nav2_indoor_launch.py use_sim_time:=true
```

`skd1_gz_nav2_launch.py` starts, in this order, `twist_mux`, the joystick teleop, both EKFs, the
`slam_toolbox` `online_async_launch.py` (with `mapper_params_online_async.yaml`) and the Nav2
bringup (`skd1_navigation/launch/navigation_launch.py` with `nav2_params.yaml`). Everything is
launched with `use_sim_time:=true`. Add `world_path:=...` to the first command to use a different world,
as explained in [Setting Up The Robot in Gazebo](../simulation/setup_gazebo.md).

### Real robot

``` shell
# On the robot
ros2 launch skd1_bringup skd1_nav2_indoor_launch.py

# On a remote computer in the same ROS domain
ros2 launch skd1_rviz skd1_rviz_nav2_indoor_launch.py use_sim_time:=false
```

`skd1_nav2_indoor_launch.py` starts the controllers (`skd1_control_launch.py`), the teleop,
the Phidgets IMU, the RPLidar C1 with its range filter, both EKFs, SLAM and Nav2. Before running
it, make sure that the sensors work as described in the previous guide.

> [!NOTE]
> `skd1_navigation/launch/navigation_launch.py` is a copy of `nav2_bringup`'s launch file
> adapted for SKD-1. Most servers run with the `cmd_vel` output remapped to `cmd_vel_nav`, which
> is one of the inputs of `twist_mux`. For outdoor operation, see `navigation_outdoor_launch.py` and
> `nav2_outdoor_params.yaml` in the same package and `skd1_nav2_outdoor_launch.py` in `skd1_bringup`.

## Verification

Drive the robot a short distance with the joystick, and check the following:

``` shell
ros2 topic echo /map --once --field info
ros2 run tf2_ros tf2_echo map odom
ros2 run tf2_ros tf2_echo map base_link
```

In RViz, `/map` should be growing as the robot moves. `map` => `odom` should only start to be
published after SLAM produces its first `/pose`; if it never shows up, check that `slam_toolbox` is
running and that `/pose` has publishers (`ros2 topic info /pose`).

To see the maps and costmaps in RViz (the provided `nav2_indoor.rviz` already has them), click **Add**,
go to **By topic** and select:

-   **Map** under `/map`
-   **Map** under `/global_costmap/costmap`, with the **Fixed Frame** set to `map`
-   **Map** under `/local_costmap/costmap`, with the **Fixed Frame** set to `odom`

<!-- TODO(screenshot): /map and global costmap of SKD-1 in the TurtleBot3 world -->
<!-- TODO(screenshot): local costmap around SKD-1 -->

When you are happy with the map, save it:

``` shell
ros2 run nav2_map_server map_saver_cli -f my_map
```

## Localization on a Saved Map

SKD-1 is currently set up to run SLAM while navigating. The ingredients for AMCL exist, but they are not wired
together:

-   `nav2_params.yaml` contains an `amcl` section (`scan_topic: scan`, `base_frame_id: base_footprint`,
    `global_frame_id: map`).
-   `skd1_nav2_indoor_launch.py` has a commented-out `nav2_amcl_localization_launch` that expects a map file
    in `skd1_navigation/maps/`, but that directory does not exist in the repository.

If you enable AMCL, remember that it publishes `map` => `odom` itself, which would conflict with the global EKF. Either run
AMCL with `tf_broadcast: false` and feed `/amcl_pose` to the global EKF as its `pose0`, or don't run the global EKF.
The alternative is to keep `slam_toolbox` and change its `mode` to `localization`, with `map_file_name` set to a map
serialized by `slam_toolbox`.

## Conclusion

SKD-1 builds its map with `slam_toolbox` while the global EKF turns the SLAM pose into the
`map` => `odom` transform, and Nav2's costmaps combine the map with live lidar data. In the next guides we
configure the robot's footprint and the planner and controller plugins.

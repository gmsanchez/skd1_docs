# Fusing Odometry with Robot Localization

In this guide we discuss how SKD-1 fuses its sources of odometry using the `robot_localization`
package, and how the `odom` => `base_link` and `map` => `odom` transforms are published.

The `robot_localization` package provides a fused and locally accurate smooth odometry from
`N` sources, which can be `nav_msgs/Odometry`, `sensor_msgs/Imu`,
`geometry_msgs/PoseWithCovarianceStamped` and `geometry_msgs/TwistWithCovarianceStamped`
messages. The fusion is done by a state estimation node, either an Extended Kalman Filter
(`ekf_node`) or an Unscented Kalman Filter (`ukf_node`). The package also has a
`navsat_transform_node` that converts GPS data into the robot's world frame.

> [!NOTE]
> **See also:**
> The [robot_localization documentation](http://docs.ros.org/en/melodic/api/robot_localization/html/index.html).

SKD-1 runs **two EKF nodes**, which is the arrangement recommended by the package for robots that have both a continuous
local estimate and a global one:

| | Local EKF | Global EKF |
|---|---|---|
| Node name | `ekf_filter_node` | `ekf_global_map_filter_node` |
| Config | `skd1_localization/config/ekf.yaml` | `skd1_localization/config/ekf_global_map.yaml` |
| Launch | `ekf_launch.py` | `ekf_global_map_launch.py` |
| `world_frame` | `odom` | `map` |
| Publishes TF | `odom` => `base_link` | `map` => `odom` |
| Output topic | `odometry/local` (remapped from `odometry/filtered`) | `odometry/global` (remapped from `odometry/filtered`) |
| Rate | 20 Hz | 10 Hz |

Nav2 consumes `odometry/global` (`odom_topic` in `nav2_params.yaml`).

## The IMU

The orientation estimate comes from the Phidgets Spatial IMU, which is configured in
`skd1_sensors/phidgets_spatial_bringup`. The raw sensor data goes through the Madgwick filter
(`imu_filter_madgwick`), which adds orientation. Both nodes run as composable nodes in a
single container in the `phidgets_373223` namespace
(`spatial_imu_filter_component_launch.py`), so the EKF receives `phidgets_373223/imu/data`.
The filter does not use the magnetometer by default (`use_mag:=false`), which is best indoors.
For outdoor use pass `use_mag:=true`. See [Setting Up Sensors](../sensors/setup_sensors.md).

## Configuring the Local EKF

`ekf.yaml` is the standard `robot_localization` example with comments, trimmed down to what is used.
The effective settings are:

| Parameter | Value | Explanation |
|---|---|---|
| `frequency` | 20.0 | Same as the controller rate. |
| `two_d_mode` | `true` | SKD-1 operates on a plane, so Z, roll and pitch are ignored. |
| `publish_tf` | `true` | This node publishes `odom` => `base_link`. |
| `world_frame` | `odom` | Continuous fusion of wheel odometry and IMU. |
| `print_diagnostics` | `true` | Publishes to `/diagnostics` if something is wrong. |

### Odometry input

``` yaml
odom0: /skd1_base_controller/odom
odom0_config: [false, false, false,    # x, y, z
               false, false, false,    # roll, pitch, yaw
               true,  true,  false,    # vx, vy, vz
               false, false, true,     # vroll, vpitch, vyaw
               false, false, false]    # ax, ay, az
```

Only velocities are fused from the wheel odometry (`vx`, `vy` and the yaw rate), and not the
integrated pose, which would otherwise drift and be counted twice. The `vy` term is included
because a skid-steer robot slides sideways during turns; the controller's `vy` is zero, and the
EKF uses this as a measurement that the robot is not moving sideways.

### IMU input

``` yaml
imu0: /imu/data      # remapped to phidgets_373223/imu/data in ekf_launch.py
imu0_config: [false, false, false,
              true,  true,  true,
              false, false, false,
              true,  true,  true,
              false, false, false]
imu0_differential: true
imu0_relative: true
imu0_remove_gravitational_acceleration: true
```

The IMU contributes orientation and angular velocity. With `two_d_mode` only yaw and yaw rate
effectively remain. Setting `differential` to `true` converts the orientation into velocities,
and `relative` makes the first measurement the zero reference, so the filter does not depend on
the absolute heading of the IMU (which needs the magnetometer to be correct).

> [!NOTE]
> **See also:**
> [Preparing Your Data](http://docs.ros.org/en/melodic/api/robot_localization/html/preparing_sensor_data.html)
> and [Configuring robot_localization](http://docs.ros.org/en/melodic/api/robot_localization/html/configuring_robot_localization.html).

## Configuring the Global EKF

The global EKF adds a source of absolute position. In `ekf_global_map.yaml`:

-   `world_frame` is `map`, so it publishes `map` => `odom`.
-   `odom0: /odometry/local` provides the local estimate with `differential: true` for x, y,
    yaw and the velocities.
-   `pose0: /pose` is an absolute x, y, yaw measurement. This is the pose that `slam_toolbox`
    publishes after it matches each scan against the map.

This is why `slam_toolbox` has its own transform broadcast disabled (`transform_publish_period: 0.0`).
SLAM provides a measurement, and the filter provides the smooth transform. You can check that
`/pose` exists with `ros2 topic info /pose` while SLAM is running.

## Outdoor Operation: Dual EKF with GPS

For outdoor operation there is an alternative configuration in `dual_ekf_navsat.yaml`, started by
`dual_ekf_navsat_launch.py` and used by `skd1_bringup/launch/skd1_nav2_outdoor_launch.py`, which has
the three nodes of the standard `robot_localization` GPS setup:

-   `ekf_filter_node_odom` (world frame `odom`, 30 Hz): fuses wheel velocity and IMU, as the local EKF above.
-   `navsat_transform`: converts the GPS fix to an `odometry/gps` message in the map frame.
-   `ekf_filter_node_map` (world frame `map`, 30 Hz): fuses wheel velocity, IMU and the x, y of `odometry/gps`.

In this mode GPS replaces SLAM as the absolute source. The F9P driver is in
`skd1_sensors/f9p_ublox`.

## Build, Run and Verification

In simulation, launch the robot first and then the EKFs, using `use_sim_time`:

``` shell
ros2 launch skd1_gz skd1_gz_turtlebot3_world_launch.py
ros2 launch skd1_localization ekf_launch.py use_sim_time:=true
```

(`skd1_gz_nav2_launch.py` launches both EKFs together with SLAM and Nav2.)

Check that the local filter has its inputs and outputs:

``` shell
ros2 node info /ekf_filter_node
ros2 topic echo /odometry/local --once
ros2 run tf2_ros tf2_echo odom base_link
```

`ros2 node info` should list `/skd1_base_controller/odom` and `/phidgets_373223/imu/data`
as subscribers, and `/odometry/local` and `/tf` as publishers. If the filter is not producing
output, check `ros2 topic echo /diagnostics`.

Drive the robot a few meters and then compare `/odometry/local` against `/ground_truth/odometry` in
simulation. The difference is the odometry error you would expect from the estimate alone.

> [!NOTE]
> In simulation, Gazebo does not publish `/tf` (it is not bridged, see
> [Setting Up The Robot in Gazebo](../simulation/setup_gazebo.md)), so the EKF is the only publisher
> of `odom` => `base_link`, as on the real robot. If you see two publishers, something was bridged by mistake.

## Conclusion

SKD-1 fuses wheel velocity with IMU data in a local EKF that publishes `odom` => `base_link`,
and a global EKF that takes SLAM (or GPS outdoors) as an absolute measurement and publishes `map` => `odom`.
Next we look at the sensors that feed all of this.

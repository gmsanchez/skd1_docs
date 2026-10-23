# Setting Up Navigation Plugins

In this guide we discuss how a robot uses different planner and controller algorithms to complete
navigation tasks, which plugins are available and for which robots they are suited, and which ones SKD-1 uses.

## Planner and Controller Servers

Navigation algorithms in Nav2 are plugins hosted by ROS action servers: the planner, the controller
and the behavior servers, among others. This guide covers the first two, which are the heart of the
navigation stack.

The **planner server** computes the robot's path, for example the shortest path between two
locations. The **controller server** generates the control commands that make the robot follow
that path, avoid dynamic obstacles on the way, and so on. Both host a map of one or more plugins,
and the behavior tree (or an application server) selects which one runs for a given task.

> [!NOTE]
> **See also:**
> [Navigation Servers](https://docs.nav2.org/concepts/index.html#navigation-servers).

## Selecting the Algorithm Plugins

> [!NOTE]
> The plugins are not limited to those mentioned here. See the
> [Navigation Plugins](https://docs.nav2.org/plugins/index.html) list and the tutorials on
> [writing a planner](https://docs.nav2.org/plugin_tutorials/docs/writing_new_nav2planner_plugin.html) and
> [writing a controller](https://docs.nav2.org/plugin_tutorials/docs/writing_new_nav2controller_plugin.html) plugin.

### Planner Server

Grid-search planners (`NavFn`, `Smac Planner 2D`, `Theta Star`) search the cost grid. They are best used on
robots that can drive in any direction or rotate in place, that is **circular differential and circular
omnidirectional** robots. They do not guarantee a drivable path for non-circular robots in tight spaces, since
they check collisions per grid cell. `Smac Hybrid-A*` supports arbitrary-shaped **Ackermann and legged**
robots using the full footprint and a minimum turning radius. `Smac Lattice` expands a state lattice and supports
**differential, omnidirectional and Ackermann** vehicles of any shape.

| Plugin Name | Supported Robot Types |
|---|---|
| NavFn Planner | Circular Differential, Circular Omnidirectional |
| Smac Planner 2D | Circular Differential, Circular Omnidirectional |
| Theta Star Planner | Circular Differential, Circular Omnidirectional |
| Smac Hybrid-A* Planner | Non-circular or Circular Ackermann, Non-circular or Circular Legged |
| Smac Lattice Planner | Non-circular Differential, Non-circular Omnidirectional |

### Controller Server

| Plugin Name | Supported Robot Types | Task |
|---|---|---|
| DWB controller | Differential, Omnidirectional | Dynamic obstacle avoidance |
| TEB Controller | Differential, Omnidirectional, Ackermann, Legged | |
| RPP controller | Differential, Ackermann, Legged | Exact path following |
| MPPI controller | Differential, Ackermann, Legged, Omnidirectional | Modern MPC controller |
| VP controller | Differential, Ackermann, Legged | High speed path tracking |

All of them work for circular and non-circular robots.

## What SKD-1 Uses

SKD-1 is a non-circular, skid-steer robot, which Nav2 treats as a differential-drive robot. The choices
in `skd1_navigation/config/nav2_params.yaml` are:

| Server | Plugin | Main settings |
|---|---|---|
| `planner_server` (`GridBased`) | `nav2_navfn_planner::NavfnPlanner` | `use_astar: true`, `tolerance: 0.5`, `allow_unknown: false` |
| `smoother_server` (`simple_smoother`) | `nav2_smoother::SimpleSmoother` | `max_its: 1000`, `do_refinement: True` |
| `controller_server` (`FollowPath`) | `nav2_regulated_pure_pursuit_controller::RegulatedPurePursuitController` | see below |
| `behavior_server` | `Spin`, `BackUp`, `DriveOnHeading`, `Wait`, `AssistedTeleop` | defaults |
| `velocity_smoother` | `nav2_velocity_smoother` | `OPEN_LOOP` feedback, 20 Hz |
| `collision_monitor` | `nav2_collision_monitor` | `FootprintApproach` polygon, `time_before_collision: 1.2` |

The controller server runs at 10 Hz with a `SimpleProgressChecker` (0.5 m of movement in 10 s) and a `SimpleGoalChecker`
(`xy_goal_tolerance: 0.25`, `yaw_goal_tolerance: 0.25`). The Regulated Pure Pursuit controller is
configured as follows:

| Parameter | Value | Explanation |
|---|---|---|
| `max_linear_vel` / `min_linear_vel` | 0.5 / -0.5 m/s | Lower than the 0.75 m/s limit of `diff_drive_controller`. |
| `max_angular_vel` | 2.5 rad/s | Lower than the controller's 3.14 rad/s. |
| `lookahead_dist` | 0.6 m (0.3 to 0.9 m) | Fixed lookahead (`use_velocity_scaled_lookahead_dist: false`). |
| `use_rotate_to_heading` | `true` | Rotate in place when the heading error is above `rotate_to_heading_min_angle` (0.785 rad), at 1.8 rad/s. |
| `allow_reversing` | `false` | |
| `use_regulated_linear_velocity_scaling` | `true` | Slows down in tight curves (`regulated_linear_scaling_min_radius: 0.9 m`, minimum speed 0.25 m/s). |
| `use_collision_detection` | `true` | Look ahead up to 1.0 s for collisions. |

### Why these choices fit SKD-1

-   **Regulated Pure Pursuit** is suited to differential robots and follows the planned path
    closely, which matches the guidance in the table above. It can rotate to the path heading
    before moving, which suits a robot that can turn in place.
-   **NavFn** is the planner the table recommends for *circular* differential robots. SKD-1 uses it with a
    rectangular footprint, so the global plan does not check the polygon. The inflation layer is what keeps
    the path away from walls, and the collision monitor and the controller's collision detection use the real
    footprint at run time. For narrow spaces, `Smac Lattice` is the plugin the table lists for
    non-circular differential robots, so it is the natural next step if NavFn paths prove too tight.
-   Skid steering makes in-place rotation scrub the wheels. If you see jerky turns or poor odometry
    in rotation, check `rotate_to_heading_angular_vel`, the angular acceleration limits and the
    `wheel_separation_multiplier` (see [Setting Up Odometry](../odom/setup_odom.md)).

### Velocity limits across the stack

The velocity limits are set in several places and the **lowest one wins**, so keep them consistent:

| Where | Linear | Angular |
|---|---|---|
| RPP controller (`nav2_params.yaml`) | 0.5 m/s | 2.5 rad/s |
| `diff_drive_controller` (`diff_drive_controller.yaml`) | 0.75 m/s | 3.14 rad/s |
| Velocity smoother (`nav2_params.yaml`) | 1.5 m/s | 3.5 rad/s |
| Joystick (`logitech_f710.config.yaml`) | 0.5 m/s (1.0 turbo) | 1.57 rad/s (3.14 turbo) |

The velocity smoother limits are higher than what the robot can do, so in practice the RPP and
`diff_drive_controller` limits are the ones that apply.

### Lifecycle management

Nav2 servers are lifecycle nodes. `skd1_navigation/launch/navigation_launch.py` lists them in
`lifecycle_nodes` and starts them with `autostart:=true`: `controller_server`, `smoother_server`,
`planner_server`, `route_server`, `behavior_server`, `velocity_smoother`, `collision_monitor`,
`bt_navigator`, `waypoint_follower` and `docking_server`. Check their states with:

``` shell
ros2 lifecycle list /controller_server
```

## Conclusion

SKD-1 uses NavFn for global planning, a simple smoother, and Regulated Pure Pursuit for path following, with a velocity
smoother and a collision monitor between the controller and the base. We also saw how the velocity limits interact across the stack. Further tuning is
covered in the [Nav2 tuning guide](https://docs.nav2.org/tuning/index.html).

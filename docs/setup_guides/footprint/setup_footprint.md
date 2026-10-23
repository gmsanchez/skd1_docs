# Setting Up the Robot's Footprint

In this guide we discuss how the footprint of SKD-1 is configured for the Nav2 navigation
algorithms, compare it with the real geometry of the robot, and visualize it in RViz.

## Footprint Introduction

The footprint outlines the robot's 2D shape when projected to the ground. Nav2 mainly uses it to
avoid collisions: the planning and control algorithms make sure that the robot does not collide
with obstacles in the costmap.

It is set with the `footprint` or `robot_radius` parameter of the global and local costmaps. The
`footprint` is an ordered vector of 2D points in the `base_link` frame (the first and last
points are joined to close the polygon). `robot_radius` generates a circle centered at
`base_link`. If both are defined, `footprint` is used.

For the global costmap, the choice depends on the robot, its environment and the path planner. For
instance, `NavFn` assumes a circular robot and checks collisions per grid cell, so a circle
is enough, while Smac Hybrid-A* checks the full polygon. For the local costmap, non-circular
robots normally use a polygon, unless computing resources are very limited or the
robot is very small relative to its environment.

The footprint can also be changed at runtime through the costmap's `~/footprint` topic, for example when a
payload changes the robot's shape.

## SKD-1 Footprint Configuration

In `skd1_navigation/config/nav2_params.yaml`, both costmaps use the same rectangular polygon centered on
`base_link`, and `robot_radius` is commented out:

``` yaml
footprint: "[ [0.25, 0.20], [0.25, -0.20], [-0.25, -0.20], [-0.25, 0.20] ]"
# robot_radius: 0.35
```

This is a 0.50 m × 0.40 m rectangle. The collision monitor also takes its footprint from the local
costmap (`footprint_topic: /local_costmap/published_footprint`), so there is a single definition to maintain.

### Comparing with the real geometry

These numbers come from `skd1_description/urdf/skd1_core.urdf.xacro`:

| Extent (from `base_link`) | Value |
|---|---|
| Chassis half-length (x) | 0.205 m |
| Chassis half-width (y) | 0.130 m |
| Outer face of the wheels (y) | 0.2153 m (track 0.37068 / 2 + wheel width 0.06 / 2) |
| Front/rear face of the wheels (x) | 0.1676 m (wheelbase 0.21524 / 2 + wheel radius 0.06) |
| Footprint half-length (x) | 0.25 m |
| Footprint half-width (y) | 0.20 m |

In the length direction the footprint has a margin of 4.5 cm beyond the chassis. In the width
direction the widest part of SKD-1 is the wheels, whose outer faces are at 0.2153 m, which is
**1.5 cm outside** the footprint's half-width of 0.20 m. If this is intentional (for instance, to
keep inflation more permissive in narrow passages), it is worth documenting here; otherwise,
consider widening the footprint to about 0.22 m. You can verify this visually: add the `RobotModel`
and the footprint `Polygon` in RViz at the same time and compare them (see below).

A circular footprint would be a conservative option. The smallest circle around the wheels and the chassis
corners has a radius of about 0.30 m (√(0.2153² + 0.205²)); the commented-out `robot_radius: 0.35` is
larger than this.

> [!NOTE]
> The footprint is not the same thing as the lidar's `footprint_laser_filter` (`inscribed_radius: 0.15`),
> which removes scan points that hit the robot body, or the minimum ranges of the costmap observation
> sources (0.20 m local, 0.30 m global). These three are related but configured separately.

## Build, Run and Verification

Start the simulation and Nav2 as described in [Mapping and Localization](../sensors/mapping_localization.md):

``` shell
ros2 launch skd1_gz skd1_gz_turtlebot3_world_launch.py
ros2 launch skd1_gz skd1_gz_nav2_launch.py
ros2 launch skd1_rviz skd1_rviz_nav2_indoor_launch.py use_sim_time:=true
```

To visualize the footprint of the local costmap, click **Add**, go to the **By topic** tab and
select **Polygon** under `/local_costmap/published_footprint`. Set the **Fixed Frame** to `odom`.
For the global costmap, add **Polygon** under `/global_costmap/published_footprint` with the
**Fixed Frame** set to `map`.

Also add the **RobotModel** display (the description topic is `/robot_description`) to compare the polygon against the robot.

<!-- TODO(screenshot): footprint polygon over the SKD-1 RobotModel, top view -->

## Conclusion

SKD-1 uses a 0.50 m × 0.40 m rectangular footprint in both costmaps. We compared it with the geometry
in the URDF and found that it covers the chassis with a margin but is slightly narrower than the
wheel track. Check that against your intent before relying on it in tight spaces.

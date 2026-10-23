# Migration notes

How the Nav2 setup guides in
[sam_bot_jazzy](https://github.com/gmsanchez/sam_bot_jazzy/blob/main/setup_guides/index.md)
were adapted to SKD-1, what was left out, and what needs attention in the SKD-1 repositories.

## Guide mapping

| Original guide (sam_bot_jazzy) | New guide | What changed |
|---|---|---|
| (none) | `docs/setup_guides/workspace/setup_workspace.md` | **New.** SKD-1 spans six repositories, so a workspace, dependency and build guide is needed first. |
| `transformation/setup_transforms.md` | `transformation/setup_transforms.md` | Concepts kept. Demo uses SKD-1's real lidar offset. Added the real SKD-1 frame tree and who publishes each transform. |
| `urdf/setup_urdf.md` | `urdf/setup_urdf.md` | Rewritten as a walkthrough of the modular xacro in `skd1_description` (`is_sim` switch, skid-steer wheel macro, meshes, collision boxes, sensor frames). |
| `sdf/setup_sdf.md` | `simulation/setup_gazebo.md` | **Replaced.** SKD-1 has no SDF. It spawns from the URDF with `<gazebo>` tags, so the guide now explains that approach, the worlds and the bridge. |
| `odom/setup_odom_gz.md` | `odom/setup_odom.md` | Replaced the Gazebo `DiffDrive` plugin and `/odom` bridge with the real chain: firmware, `skd_base`, `diff_drive_controller` (with skid-steer calibration), `twist_mux`. |
| `odom/setup_robot_localization.md` | `odom/setup_robot_localization.md` | Rewritten for the two-EKF setup (local and global) and the outdoor dual EKF with `navsat_transform`. |
| `sensors/setup_sensors_gz.md` | `sensors/setup_sensors.md` | Real RPLidar C1, Phidgets IMU and F9P GPS, with laser filters. Depth camera section removed (SKD-1 has no camera). |
| `sensors/mapping_localization.md` | `sensors/mapping_localization.md` | Uses SKD-1's `nav2_params.yaml` and `mapper_params_online_async.yaml`, and documents that the global EKF (not SLAM) publishes `map` => `odom`. |
| `footprint/setup_footprint.md` | `footprint/setup_footprint.md` | Uses SKD-1's rectangular footprint and compares it with the URDF geometry. |
| `algorithm/select_algorithm.md` | `algorithm/select_algorithm.md` | Kept the general tables. Added what SKD-1 actually uses (NavFn, RPP) and a cross-stack velocity limits table. |

## Not carried over

-   `setup_odom_gz_classic.*` and `setup_sensors_gz_classic.*`: Gazebo Classic is for ROS 2 Humble and older.
-   All `.rst` files: only the Markdown versions are kept. The site is built with Sphinx + MyST from the Markdown.
-   The `sam_bot_description` package and its `sam_bot` images (Gazebo and RViz screenshots).
    Generic images were kept: the three TF diagrams and the four sensor-message images.

## Screenshots to take

The guides have `TODO(screenshot)` comments where an SKD-1 image should go:

| Guide | Screenshot |
|---|---|
| Transformations | `view_frames` output |
| URDF | SKD-1 in RViz (RobotModel + TF) |
| Gazebo | SKD-1 in the TurtleBot3 world |
| Sensors | LaserScan in RViz |
| Mapping and localization | `/map` with global costmap; local costmap |
| Footprint | Footprint polygon over the RobotModel |

Search with `grep -rn "TODO(screenshot)" docs`.

## Issues found in the SKD-1 repositories

These came up while writing the guides. None blocks the documentation, but they are worth fixing:

1.  **`skd1_visualization`: `model.rviz` is missing.** `skd1_rviz/launch/view_model_launch.py` loads
    `rviz/model.rviz`, but only `nav2_indoor.rviz` and `nav2_outdoor.rviz` exist.
2.  **Undeclared dependencies.** The `package.xml` of `skd1_localization` and `skd1_navigation` have no
    `<exec_depend>` for `robot_localization`, `slam_toolbox` or `nav2_*`, and `skd1_bringup` does not list
    `skd1_description`, `skd1_localization` or `skd1_navigation`. `rosdep` will not install them.
3.  **Footprint narrower than the wheels.** The costmap polygon half-width (0.20 m) is 1.5 cm inside the
    outer face of the wheels (0.2153 m). See the footprint guide.
4.  **Firmware board naming.** The `skd1` README says "Blue Pill", while `platformio.ini` builds for the
    `blackpill_f411ce` board in an environment named `bluepill_f103c8`.
5.  **Machine-specific paths and addresses** in `skd1_configure_ros2_environment.sh` and
    `skd1_launch_fastdds_server.sh` (`/home/ubuntu/...`, `192.168.1.100`).
6.  **Leftover commented-out code.** `wheel.urdf.xacro` has a commented-out transmission block, and
    `skd1_nav2_indoor_launch.py` has a commented-out AMCL launch that points to a
    `maps/turtlebot3_world.yaml` that does not exist. These can confuse newcomers.
7.  **Short READMEs.** `hibachi_firmware`, `skd1_simulation` and `skd1_sensors` have one-line READMEs. Once
    this repo is published, linking each of them back here would help.

## Not verified

-   The commands were written from reading the code and configs. They were **not run**, because ROS 2 and
    Gazebo are not available where this was written. Run through each guide once in simulation, then on the robot.
-   The apt package names in the workspace guide follow the usual Jazzy names. Check them with `apt-cache policy`.
-   `skd1_extra` (design files, BoM, bag file) was not available, so it is only linked.

## Notes on the site build

-   The guides live under `docs/setup_guides/`. `MIGRATION.md` is at the repository root on purpose, so it
    is **not** published on the site (it lists open issues of the SKD-1 repositories).
-   The Mermaid diagrams are drawn in the browser with JavaScript loaded from the jsDelivr CDN, so they need
    internet access when viewed. The Markdown source and GitHub's own rendering are not affected.
-   `intersphinx` (automatic links to ROS and Nav2 pages) is not configured: it only helps with Sphinx
    cross-reference roles, not with the plain Markdown links used here.

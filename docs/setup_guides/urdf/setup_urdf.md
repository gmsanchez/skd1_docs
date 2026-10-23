# Setting Up The URDF

> [!NOTE]
> URDF is used to set up the robot frames and describe the robot's structure at run-time, on
> hardware and in simulation. Unlike the original Nav2 guides, SKD-1 does **not** maintain a
> separate SDF file. Gazebo reads the same URDF, extended with `<gazebo>` blocks, so the whole
> robot is described once. See [Setting Up The Robot in Gazebo](../simulation/setup_gazebo.md).

In this guide we walk through the Unified Robot Description Format (URDF) of SKD-1, which is
written with Xacro and lives in the `skd1_description` package of the
[skd1](https://github.com/gmsanchez/skd1) repository. We will see how it is organized, what
each part defines, how to view the model in RViz, and which properties you need to change when
the robot changes.

## URDF and the Robot State Publisher

As discussed in the previous guide, Nav2 needs the transforms from `base_link` to every sensor
and reference frame. Instead of one `static_transform_publisher` per frame we use the
`robot_state_publisher`, which reads the URDF and publishes every transform that can be
inferred from the robot's structure. For continuous joints (the wheels) it combines the URDF
with `/joint_states`.

The URDF is an XML file that also describes visual shapes (used by RViz and Gazebo), collision
shapes, and inertial properties (used by physics simulators). Xacro adds properties and macros
to avoid repetition. SKD-1 uses all of these.

> [!NOTE]
> **See also:**
> [URDF documentation](https://docs.ros.org/en/jazzy/Tutorials/Intermediate/URDF/URDF-Main.html)
> and [Robot State Publisher](https://github.com/ros/robot_state_publisher).

## File Layout

All files are in `skd1_description/urdf/`:

| File | Purpose |
|---|---|
| `skd1.urdf.xacro` | Top-level file. Declares the `is_sim` argument and includes the other files. |
| `skd1_core.urdf.xacro` | Robot geometry: chassis, wheels, sensors, constants. Identical for simulation and hardware. |
| `wheel.urdf.xacro` | The `skd1_wheel` macro, instantiated four times. |
| `inertial_macros.xacro` | `inertial_box`, `inertial_cylinder`, `inertial_sphere` and `dummy_inertial`. |
| `ros2_control.urdf.xacro` | `ros2_control` hardware description for the **real robot** (`skd_base/SKDHardware`). |
| `skd1_sim_ros2_control.urdf.xacro` | `ros2_control` description for **Gazebo** plus the controller and odometry plugins. |
| `skd1_sim_sensors.urdf.xacro` | Gazebo sensor definitions (IMU, magnetometer, lidar, GPS). |

The top-level file shows the structure at a glance:

``` xml
<xacro:arg name="is_sim" default="true"/>

<xacro:include filename="$(find skd1_description)/urdf/skd1_core.urdf.xacro" />

<xacro:if value="$(arg is_sim)">
    <xacro:include filename="$(find skd1_description)/urdf/skd1_sim_ros2_control.urdf.xacro" />
    <xacro:include filename="$(find skd1_description)/urdf/skd1_sim_sensors.urdf.xacro" />
</xacro:if>

<xacro:unless value="$(arg is_sim)">
    <xacro:include filename="$(find skd1_description)/urdf/ros2_control.urdf.xacro" />
</xacro:unless>
```

The launch file `skd1_description/launch/skd1_description_launch.py` runs `xacro` on this
file and passes the result to `robot_state_publisher`. It reuses the `use_sim_time` launch
argument as `is_sim`, so one flag selects both the clock and the hardware interface.

## Constants

The core file starts with the dimensions of the robot as Xacro properties. These are the values
to edit if you modify the mechanics:

| Property | Value | Meaning |
|---|---|---|
| `wheel_distance` | 0.21524 m | Distance between front and rear axles (wheelbase) |
| `wheel_separation` | 0.37068 m | Distance between left and right wheel centerlines (track) |
| `wheel_height` | 0.0328 m | Height of the axles below `base_link` |
| `wheel_radius` / `wheel_width` / `wheel_mass` | 0.06 m / 0.06 m / 0.150 kg | Wheel dimensions and mass |
| `chassis_x_size` / `_y_size` / `_z_size` | 0.410 / 0.260 / 0.094 m | Chassis box used for collision and inertia |

## Links and Frames

`base_link` is located at the geometric center of the chassis, on top of the acrylic plate.
Its visual is a mesh (`meshes/skd1_chassis.stl`). Its collision is built from simple boxes
instead of the mesh: the chassis, the antenna deck, and four motor covers. Simple collision
shapes are faster and more robust in physics simulation.

`base_footprint` is a non-physical link on the ground below `base_link`, 0.0928 m lower
(`wheel_height + wheel_radius`). It has a `dummy_inertial` so that physics engines do not complain.

`inertial_link` holds the inertial properties of the whole robot (a 5 kg box). The Nav2 guide
notes that the `kdl_parser` used by `robot_state_publisher` does not like inertia on the root
link; SKD-1 follows the same advice by keeping the inertia in a separate link attached to
`base_link` by a fixed joint.

Wheels use the `skd1_wheel` macro. Instead of the `x_reflect`/`y_reflect` parameters of the
original guide, the macro receives the joint pose as a Xacro block parameter:

``` xml
<xacro:skd1_wheel wheel_prefix="front_left">
    <origin xyz="${wheel_distance/2} ${wheel_separation/2} -${wheel_height}" rpy="0 0 0" />
</xacro:skd1_wheel>
```

This creates `front_left_wheel_link` and a `continuous` joint `front_left_wheel_joint` rotating
about the Y axis. The same is done for `front_right`, `rear_left` and `rear_right`. These joint
names must match those used in the `ros2_control` description and in
`skd1_control/config/diff_drive_controller.yaml`.

Sensor frames are fixed links on `base_link`:

| Frame | Sensor | Position (x, y, z) in `base_link` |
|---|---|---|
| `phidgets_imu_link` | Phidgets Spatial IMU | 0, 0, 0.0732 |
| `rplidar_link` | Slamtec RPLidar C1 | 0.075, 0, 0.1238 (rotated by π in yaw) |
| `ardusimple_gps_link` | ArduSimple (u-blox F9P) antenna | 0, 0.055, 0.282 |
| `m8n_gps_link` | u-blox M8N GPS | 0, -0.055, 0.282 |

When you add a sensor, you need to add the link and fixed joint here, and then a matching sensor block in
`skd1_sim_sensors.urdf.xacro` if you want it in simulation.

> [!NOTE]
> The URDF references meshes with `file://$(find skd1_description)/meshes/...`, so the
> `meshes` folder must be installed. `skd1_description/CMakeLists.txt` already installs
> `launch`, `meshes` and `urdf`.

## Check the URDF

You can expand the Xacro and check the result without launching anything. Use `is_sim:=false`
for the hardware version or `is_sim:=true` for the simulation version:

``` shell
sudo apt install liburdfdom-tools
xacro $(ros2 pkg prefix skd1_description)/share/skd1_description/urdf/skd1.urdf.xacro is_sim:=false > /tmp/skd1.urdf
check_urdf /tmp/skd1.urdf
```

`check_urdf` prints the link tree rooted at `base_link`.

## Visualization using RViz

Build and source the workspace, then launch the robot state publisher:

``` shell
ros2 launch skd1_description skd1_description_launch.py
```

In a second terminal, start the joint state GUI so the wheel joints have values, and RViz:

``` shell
ros2 run joint_state_publisher_gui joint_state_publisher_gui
rviz2
```

In RViz set the **Fixed Frame** to `base_link`, then add a **RobotModel** display with the
**Description Topic** `/robot_description` and a **TF** display. You should see the chassis,
the four wheels and the sensor frames. Moving the sliders of the joint state GUI rotates the wheels.

<!-- TODO(screenshot): SKD-1 in RViz (RobotModel + TF) -->

> [!NOTE]
> `skd1_visualization/skd1_rviz/launch/view_model_launch.py` does the same with a single command
> (it starts the description, the joint state GUI and RViz), but it loads
> `skd1_rviz/rviz/model.rviz`, and that file is not present in the repository, only
> `nav2_indoor.rviz` and `nav2_outdoor.rviz` are. Until `model.rviz` is added, use the manual
> steps above. After adding it, replace this note with `ros2 launch skd1_rviz view_model_launch.py`.

To see the collision shapes, enable **Collision Enabled** under **RobotModel** and disable **Visual Enabled**.
You should see the chassis box, the tall antenna deck box, the four motor cover boxes and the
four wheel cylinders.

## Conclusion

In this guide we walked through the SKD-1 URDF: its modular Xacro files, how one `is_sim` switch
selects the simulation or hardware description, the frames and constants, and how to check and visualize
the result. Next we see how the same description is used by Gazebo.

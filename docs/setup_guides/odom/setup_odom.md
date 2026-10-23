# Setting Up Odometry

In this guide we look at how SKD-1 produces odometry for Nav2. First there is a short
introduction to odometry and to the messages and transforms Nav2 needs. Then we follow the
whole chain on SKD-1, from the wheel encoders on the STM32 microcontroller up to the
`nav_msgs/Odometry` message, and show how the same controller configuration is used on the real
robot and in Gazebo.

> [!NOTE]
> **See also:**
> The packages involved are `skd1_control` and `skd_base` in [skd1](https://github.com/gmsanchez/skd1),
> and the firmware in [hibachi_firmware](https://github.com/gmsanchez/hibachi_firmware).

## Odometry Introduction

The odometry system provides a locally accurate estimate of a robot's pose and velocity based
on its motion. It can come from IMUs, lidar, radar, visual odometry, wheel encoders and
others. IMUs drift over time while wheel encoders drift over distance traveled, so they are
often used together to compensate each other's weaknesses.

The `odom` frame uses the odometry system to provide localization that is continuous but
becomes less accurate over time or distance. It is still good for navigating the robot's
immediate vicinity (collision avoidance, for example). The globally accurate `map` frame is
used to correct the `odom` frame.

Nav2 requires the `odom` => `base_link` transform, and also a `nav_msgs/Odometry` message,
because it carries the robot's velocity:

``` shell
std_msgs/Header header
string child_frame_id
geometry_msgs/PoseWithCovariance pose
geometry_msgs/TwistWithCovariance twist
```

The `pose` is relative to `header.frame_id` and the `twist` is expressed in `child_frame_id`.

## The Odometry Chain on SKD-1

``` mermaid
graph LR
    A[Wheel encoders] --> B[hibachi_firmware STM32<br/>speed estimation + PID]
    B <-->|serial, HDLC framing| C[skd_base SKDHardware<br/>ros2_control plugin]
    C --> D[skd1_base_controller<br/>diff_drive_controller]
    D -->|/skd1_base_controller/odom| E[Local EKF]
    F[Phidgets IMU] --> E
    E -->|odom to base_link TF<br/>/odometry/local| G[Nav2]
```

Each stage:

1.  **Firmware (`hibachi_firmware`).** The STM32 counts encoder ticks for each motor, estimates
    wheel speed and runs a PID speed controller every 20 ms (`PID_UPDATE_mS`). The default PID
    gains in `Hibachi.h` are kP = 25, kI = 1, kD = 5. A command timeout of 500 ms
    (`CMD_TIMEOUT_mS`) is defined for safety. Motor drivers are in `lib/Motor`
    (`DualG2.h`, `L298N.h`) and the serial protocol is in `lib/SerialHDLC` (HDLC framing with CRC-16).
2.  **Hardware interface (`skd_base`).** `SKDHardware` is a `ros2_control` `SystemInterface`. It
    exposes four joints (`front_left_wheel_joint`, `front_right_wheel_joint`,
    `rear_left_wheel_joint`, `rear_right_wheel_joint`) with a **velocity command interface** and
    **position and velocity state interfaces**. On each cycle it reads wheel state from the
    microcontroller and writes the velocity commands over the serial port.
3.  **Controller (`skd1_control`).** `diff_drive_controller` takes velocity commands, converts
    them into wheel velocities, and computes odometry from the wheel feedback.

On the real robot, the serial connection is configured in `skd1_description/urdf/ros2_control.urdf.xacro`:

| Parameter | Value |
|---|---|
| `serial_port` | `/dev/ttyBPILL` |
| `baud_rate` | 115200 |
| `flow_control`, `parity`, `stop_bits` | none, none, 1 |
| `update_rate` | 20 (Hz) |

`/dev/ttyBPILL` is a custom device name, so the robot's computer needs a udev rule that creates
this symlink for the microcontroller. The same applies to `/dev/rplidar` and `/dev/ttyARDS` used
by the sensors. Check that these exist (`ls -l /dev/ttyBPILL`) when the hardware does not come up.

In simulation, the `skd_base` plugin is replaced by `gz_ros2_control/GazeboSimSystem`
(see [Setting Up The Robot in Gazebo](../simulation/setup_gazebo.md)), and everything from the
controller onwards is identical.

> [!NOTE]
> The skd1 README refers to a "Blue Pill" board, while `hibachi_firmware/platformio.ini` selects
> the `blackpill_f411ce` board (in an environment still named `bluepill_f103c8`). `Hibachi.h`
> supports both through `blackpill_pinout.h` and `bluepill_pinout.h`. Check which board is
> installed in your robot before flashing.

To build and flash the firmware (requires [PlatformIO](https://platformio.org/) and DFU mode on the board):

``` shell
cd hibachi_firmware
pio run -t upload
```

## Configuring the Controller

The controller is configured in `skd1_control/config/diff_drive_controller.yaml`, which is used
unchanged by the real robot and by Gazebo. The `controller_manager` runs at 20 Hz and loads two
controllers: `joint_state_broadcaster` and `skd1_base_controller`
(`diff_drive_controller/DiffDriveController`).

The kinematic parameters deserve a closer look because SKD-1 is a **skid-steer** robot:

| Parameter | Value | Explanation |
|---|---|---|
| `left_wheel_names`, `right_wheel_names` | two joints per side | The two wheels of each side get the same command. |
| `wheel_separation` | 0.34 m | Not the geometric track (0.37068 m in the URDF). See below. |
| `wheel_separation_multiplier` | 1.42 | Together with the above, an effective track of 0.34 × 1.42 = 0.4828 m. |
| `wheel_radius` | 0.06 m | 12 cm diameter wheels. |
| `left_wheel_radius_multiplier`, `right_wheel_radius_multiplier` | 1.03, 1.039 | Calibration of the effective wheel radius for each side. |

A skid-steer robot turns by skidding its wheels sideways, so its effective turning radius is
larger than the geometric distance between the wheels. Using the multiplier to enlarge the
track makes the computed yaw rate match what the robot really does. The comment in the file
notes that the value depends on the floor type. **If you change the floor, the tires or the payload,
recalibrate the multipliers:**

-   For rotation, rotate the robot in place a known number of turns. If odometry reports
    θ<sub>odom</sub> while the real rotation was θ<sub>real</sub>, set
    `wheel_separation_multiplier` to `old × θ_odom / θ_real`.
-   For distance, drive in a straight line and set each radius multiplier to
    `old × distance_real / distance_odom`.

Other relevant parameters:

| Parameter | Value | Explanation |
|---|---|---|
| `odom_frame_id`, `base_frame_id` | `odom`, `base_link` | Frames of the odometry message. |
| `enable_odom_tf` | `false` | The controller does **not** publish `odom` => `base_link`. The EKF does. |
| `open_loop` | `false` | Odometry is computed from wheel feedback, not from commands. |
| `position_feedback` | `false` | Odometry is integrated from wheel velocity, not from wheel position. |
| `velocity_rolling_window_size` | 1 | No averaging of wheel velocity. |
| `use_stamped_vel` | `true` | Commands are `geometry_msgs/TwistStamped`. |
| `cmd_vel_timeout` | 1.25 s | The robot stops if commands stop arriving. |
| `pose_covariance_diagonal`, `twist_covariance_diagonal` | 0.001 (0.01 for yaw) | Odometry covariance, used by the EKF to weight this source. |
| Linear limits | 0.75 m/s, 0.75 m/s² | Velocity and acceleration limits. |
| Angular limits | 3.14 rad/s, 1.57 rad/s² | Velocity and acceleration limits. |

The controller publishes `nav_msgs/Odometry` on `/skd1_base_controller/odom`.

## Commanding the Robot: twist_mux and Teleoperation

The controller subscribes to `/skd1_base_controller/cmd_vel`. Several sources want to drive the
robot (a joystick, a keyboard, Nav2) so they go through a `twist_mux` node, configured in
`skd1_teleop/config/twist_mux.yaml`. The highest priority input that is currently active wins:

| Input topic | Source | Priority |
|---|---|---|
| `cmd_vel_joy` | Joystick (`teleop_twist_joy`) | 100 |
| `cmd_vel_key` | Keyboard | 20 |
| `cmd_vel` | Nav2 collision monitor output, generic commands | 10 |
| `cmd_vel_nav` | Nav2 servers | 10 |

The multiplexer output is remapped to `/skd1_base_controller/cmd_vel`
(`skd1_teleop/launch/skd1_twist_mux_launch.py`). Every input times out after 0.5 s. Because the joystick has
the highest priority, you can always take over from Nav2 by pressing the enable button.

The joystick configuration (`skd1_teleop/config/logitech_f710.config.yaml`) is for a Logitech F710:
hold RB (button 5) to drive, hold LB (button 4) as well for turbo. Speeds are 0.5 m/s and
1.57 rad/s, or 1.0 m/s and 3.14 rad/s in turbo.

## Build, Run and Verification

On the real robot, `skd1_bringup` provides a launch file for just the base and teleoperation:

``` shell
ros2 launch skd1_bringup bringup_joy_teleop_launch.yaml
```

It includes `skd1_control_launch.py` (robot state publisher, `ros2_control_node`,
`joint_state_broadcaster` and, after it finishes, `skd1_base_controller`) and the two teleop launch
files. In simulation, the controllers are started by `skd1_gz_launch.py`.

Check the hardware interface and the controllers:

``` shell
ros2 control list_hardware_components
ros2 control list_controllers
```

Both controllers must be `active`. Then check the odometry and joint states, while driving:

``` shell
ros2 topic hz /skd1_base_controller/odom
ros2 topic echo /skd1_base_controller/odom --once
ros2 topic echo /joint_states --once
```

The rate should be around 20 Hz. In simulation you can also compare against the ground truth
published by the Gazebo plugin:

``` shell
ros2 topic echo /ground_truth/odometry --once
```

> [!NOTE]
> Since `enable_odom_tf` is `false`, `odom` => `base_link` will **not** exist until the EKF of
> the next guide is running. RViz will show a missing transform error if you set the fixed frame to `odom` before that.

## Conclusion

We followed odometry from the encoders to Nav2: the firmware measures and controls wheel speed,
`skd_base` exposes the wheels to `ros2_control`, and `diff_drive_controller` computes odometry
using skid-steer corrections. The commands reach the robot through `twist_mux`. In the next guide we fuse this
odometry with the IMU.

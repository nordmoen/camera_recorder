# `camera_recorder`
This ROS package helps starting and stopping video recordings.

The intended use case is for users to configure the node either through
command-line arguments or through the `~configure` service and then start and
stop individual recordings. The individual recordings could be one or several
experiment runs that needs to be recorded.

## Install
This package has a few requirements outside of ROS which needs to be installed
before building, the dependencies are listed in
[`requirements.txt`](requirements.txt) file.

```bash
$ pip install -r requirements.txt
```

## Interface
The interface for this node is mainly through the services `~start` and `~stop`.
The `~start` services takes as input the [`Record` service](srv/Record.srv)
which specifies the output filename (can also be complex path, the node will
create folders as needed) and starts the recording. The recording will continue
until either the node is shutdown or the user calls `~stop` with the [`Trigger`
service](https://docs.ros.org/api/std_srvs/html/srv/Trigger.html).  Users should
ensure that `success` is `true` after each service call to ensure that
everything went smoothly. Errors are reported in the `message` type of each
service.

If the output format is different from the input source, `ffmpeg` will transcode
on the fly. If this is not desired it is recommended to not apply any
transformations, like `hflip`, and utilize the same format as the input source.

### Configuration
The node can be configured either through parameters passed during startup, see
[`init.launch`](launch/init.launch), or through the [`~configure`
service](srv/Configure.srv) after the node is started. Configuration will take
effect the next time the `~start` service is called.

## Examples
```bash
# Start the node with 720 resolution and 30fps
$ roslaunch camera_recorder init.launch size:=1280x720 rate:=30
```

```bash
# Record from different input source in raw format
$ roslaunch camera_recorder init.launch source:=/dev/video1 format:=yuyv422
```

```bash
# Additional arguments supported by launch file
$ roslaunch camera_recorder init.launch --ros-args
```

## Checking supported streams
This package uses [`v4l2`](https://en.wikipedia.org/wiki/Video4Linux) to record
data through [`ffmpeg`](https://ffmpeg.org/). This places some restrictions on
the format of the input stream and video sizes. To query your equipment use the
following commands:

```bash
# List connected devices:
$ v4l2-ctl --list-devices
# List supported output formats, stream size and frames per second:
$ v4l2-ctl --list-formats-ext
# List supported formats for specific stream
$ ffmpeg -f v4l2 -list_formats all -i /dev/video0
```

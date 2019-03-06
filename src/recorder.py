#!/usr/bin/env python

"""ROS node that interacts with FFMPEG to record video on-demand"""

from camera_recorder.srv import Configure, Record
from std_srvs.srv import Trigger
import ffmpeg
import os
import rospy
import time


# FFMPEG configuration, used to create FFMPEG process
ffmpeg_cfg = None
# Current FFMPEG process
ffmpeg_proc = None


def configure(source, size, input_format, framerate, vflip=False, hflip=False):
    """
    Configure FFMPEG

    :param str source: Input source, e.g. '/dev/video0'
    :param (int, int) size: Width x Height of stream
    :param str input_format: Input format of webcam
    :param int framerate: Frame rate of input stream
    :param bool vflip: Flip input stream vertically
    :param bool hflip: Flip input stream horizontally
    """
    _size = "{}x{}".format(*size)
    global ffmpeg_cfg
    ffmpeg_cfg = ffmpeg.input(source, input_format=input_format,
                              framerate=framerate, video_size=_size)
    if vflip:
        ffmpeg_cfg = ffmpeg_cfg.vflip()
    if hflip:
        ffmpeg_cfg = ffmpeg_cfg.hflip()


def start_recording(output, overwrite=False):
    """
    Start a new recording

    :param str output: Path and name of output file
    :param bool overwrite: If file already exist, overwrite?
    """
    global ffmpeg_cfg, ffmpeg_proc
    full_path = os.path.abspath(output)
    directory = os.path.dirname(full_path)
    # If directory does not exist we automatically create it
    if not os.path.exists(directory):
        os.mkdir(directory)
    cfg = ffmpeg_cfg.output(full_path)
    if overwrite:
        cfg = cfg.overwrite_output()
    ffmpeg_proc = cfg.run_async(quiet=True)


def stop_recording():
    """Stop current recording"""
    global ffmpeg_proc
    # Tell process to stop
    ffmpeg_proc.terminate()
    ret = None
    for _ in range(3):
        ret = ffmpeg_proc.poll()
        if not ret:
            # If the process has not stopped we wait
            # and try again
            time.sleep(0.1)
        else:
            break
    else:
        rospy.logerr("FFMPEG did not respect 'terminate'!")
        ffmpeg_proc.kill()
    ffmpeg_proc = None


def _start_callback(req):
    """Service callback to start a new recording"""
    global ffmpeg_proc
    if not ffmpeg_proc:
        try:
            start_recording(req.output, req.overwrite)
            return {'success': True, 'message': ""}
        except Exception as e:
            # If 'start_recording' threw exception ensure that 'ffmpeg_proc'
            # is set to None so that future calls should succeed
            ffmpeg_proc = None
            return {'success': False, 'message': str(e)}
    else:
        rospy.logwarn("Asked to start recording, but there is one in progress")
        return {'success': False, 'message': "Recording already in progress"}


def _stop_callback(req):
    """Service callback to stop current recording"""
    global ffmpeg_proc
    if ffmpeg_proc:
        rospy.logdebug("Stopping current recording")
        try:
            stop_recording()
            return {'success': True, 'message': ""}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    else:
        rospy.logwarn("Asked to stop recording, but there is none in progress")
        return {'success': False, 'message': "No recording in progress"}


def _cfg_callback(req):
    """Service callback to configure FFMPEG"""
    # Note that we can always configure even though a recording is in progress
    # as the 'configure' call will only affect the 'ffmpeg_cfg' object and not
    # the 'ffmpeg_proc' instance
    try:
        configure(req.source, (req.width, req.height), req.input_format,
                  req.framerate, req.vflip, req.hflip)
        return {'success': True, 'message': ""}
    except Exception as e:
        return {'success': False, 'message': str(e)}


if __name__ == '__main__':
    rospy.init_node('camera_recorder')
    # Parse parameter for initial camera configuration
    source = rospy.get_param('~source')
    size = tuple(map(int, rospy.get_param('~size').split('x')))
    input_format = rospy.get_param('~format')
    framerate = int(rospy.get_param('~framerate'))
    vflip = bool(rospy.get_param('~vflip', False))
    hflip = bool(rospy.get_param('~hflip', False))
    # Configure camera
    configure(source, size, input_format, framerate, vflip, hflip)
    # Setup ROS service
    start = rospy.Service('~start', Record, _start_callback)
    stop = rospy.Service('~stop', Trigger, _stop_callback)
    cfg = rospy.Service('~configure', Configure, _cfg_callback)
    # Spin until exit
    rospy.spin()
    # Stop recording if in progress
    if ffmpeg_proc:
        stop_recording()

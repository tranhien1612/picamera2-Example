#!/usr/bin/env python3
# Ref: https://gist.github.com/fzwoch/701599167e3b71bd48885ba423b4b24d
# install lib
# sudo apt install gstreamer1.0-tools gstreamer1.0-plugins-base gstreamer1.0-plugins-good gstreamer1.0-plugins-bad gstreamer1.0-plugins-ugly gstreamer1.0-libav
# sudo apt install gstreamer1.0-rtsp && sudo apt install python3-gst-1.0 && sudo apt install gir1.2-gst-rtsp-server-1.0
# sudo apt install python3-gi gir1.2-gst-plugins-base-1.0 gir1.2-gstreamer-1.0
import gi

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import Gst, GstRtspServer, GLib 

Gst.init(None)

server = GstRtspServer.RTSPServer.new()
server.set_service("8554")

factory = GstRtspServer.RTSPMediaFactory.new()
factory.set_launch("videotestsrc ! x264enc ! rtph264pay name=pay0 pt=96")

mounts = server.get_mount_points()
mounts.add_factory("/test", factory)

server.attach(None)

loop = GLib.MainLoop()
print("Enter URL: rtsp://localhost:8554/test")
loop.run()

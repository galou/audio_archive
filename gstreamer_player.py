# -* coding: utf-8 -*-
# A headless media player based on gstreamer.

from gi.repository import Gst
Gst.init(None)


class Player:
    def __init__(self, uri=None):
        # Creates a playbin (plays media from an uri).
        self.player = Gst.ElementFactory.make('playbin', 'player')

        self.uri = uri

    @property
    def uri(self):
        return self._uri

    @uri.setter
    def uri(self, value):
        self._uri = value
        self.player.set_state(Gst.State.NULL)
        if value:
            self.player.set_property('uri', value)

    def play(self):
        """Start playing"""
        self.player.set_state(Gst.State.PLAYING)

    def pause(self):
        """Pause playing"""
        self.player.set_state(Gst.State.PAUSED)

    def stop(self):
        self.player.set_state(Gst.State.NULL)

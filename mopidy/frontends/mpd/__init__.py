import logging
import sys

from pykka.actor import ThreadingActor

from mopidy import settings
from mopidy.frontends.mpd import dispatcher, protocol
from mopidy.utils import network, process

logger = logging.getLogger('mopidy.frontends.mpd')

class MpdFrontend(ThreadingActor):
    """
    The MPD frontend.

    **Dependencies:**

    - None

    **Settings:**

    - :attr:`mopidy.settings.MPD_SERVER_HOSTNAME`
    - :attr:`mopidy.settings.MPD_SERVER_PORT`
    - :attr:`mopidy.settings.MPD_SERVER_PASSWORD`
    """

    def __init__(self):
        hostname = network.format_hostname(settings.MPD_SERVER_HOSTNAME)
        port = settings.MPD_SERVER_PORT

        try:
            network.Listener(hostname, port, MpdSession)
        except IOError, e:
            logger.error(u'MPD server startup failed: %s', e)
            sys.exit(1)

        logger.info(u'MPD server running at [%s]:%s', hostname, port)

    def on_stop(self):
        process.stop_actors_by_class(MpdSession)


class MpdSession(network.LineProtocol):
    """
    The MPD client session. Keeps track of a single client session. Any
    requests from the client is passed on to the MPD request dispatcher.
    """

    terminator = protocol.LINE_TERMINATOR
    encoding = protocol.ENCODING

    def __init__(self, sock, addr):
        super(MpdSession, self).__init__(sock, addr)
        self.dispatcher = dispatcher.MpdDispatcher(self)

    def on_start(self):
        self.send_lines([u'OK MPD %s' % protocol.VERSION])

    def on_line_received(self, line):
        self.send_lines(self.dispatcher.handle_request(line))

    def close(self):
        self.stop()

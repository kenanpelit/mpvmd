import logging
import asyncio
from mpv import MPV
from mpvmd import transport, settings


class Server:
    def __init__(self):
        self._handlers = {
            'play': self._handle_msg_play,
            'pause': self._handle_msg_pause,
            'play-pause': self._handle_msg_play_pause,
            'stop': self._handle_msg_stop,
        }

    def run(self, host, port, loop):
        self._mpv = MPV(ytdl=True)
        self._mpv.video = 'no'
        self._mpv.pause = True

        server = loop.run_until_complete(
            asyncio.start_server(self.server_handler, host, port, loop=loop))
        logging.info('Serving on %r', server.sockets[0].getsockname())

        try:
            loop.run_forever()
        except KeyboardInterrupt:
            pass
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()
        self._mpv.terminate()

    async def server_handler(self, reader, writer):
        try:
            request = await transport.read(reader)
            addr = writer.get_extra_info('peername')
            logging.info('Received %r from %r', request, addr)

            try:
                response = self._handlers[request['msg']](request)
            except Exception as ex:
                response = {
                    'status': 'error',
                    'code': ex.__class__.__name__,
                    'msg': str(ex)
                }

            logging.info('Send: %r', response)
            await transport.write(writer, response)

            writer.close()
        except Exception as ex:
            logging.exception(ex)


    def _handle_msg_play(self, msg):
        self._mpv.pause = False
        if 'file' in msg:
            self._mpv.play(msg['file'])

    def _handle_msg_play_pause(self, _msg):
        self._mpv.pause = not self._mpv.pause

    def _handle_msg_stop(self, _msg):
        self._mpv.pause = True
        self._mpv.seek('00:00')

    def _handle_msg_pause(self, _msg):
        self._mpv.pause = True


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    Server().run(settings.HOST, settings.PORT, loop)


if __name__ == '__main__':
    main()

import logging
import asyncio
from typing import Dict, List
from mpv import MPV
from mpvmd import transport, settings


class Command:
    name: str
    subclasses: List['Command'] = []

    def __init_subclass__(cls, **kwargs):
        Command.subclasses.append(cls())

    def run(self, server: 'Server', request) -> Dict:
        raise NotImplementedError()


class PlayCommand(Command):
    name = 'play'

    def run(self, server: 'Server', request) -> Dict:
        server.mpv.pause = False
        if 'file' in request:
            server.mpv.play(request['file'])
        return {'status': 'ok'}


class PlayPauseCommand(Command):
    name = 'play-pause'

    def run(self, server: 'Server', _request) -> Dict:
        server.mpv.pause = not server.mpv.pause
        return {'status': 'ok'}


class PauseCommand(Command):
    name = 'pause'

    def run(self, server: 'Server', _request) -> Dict:
        server.mpv.pause = True
        return {'status': 'ok'}


class StopCommand(Command):
    name = 'stop'

    def run(self, server: 'Server', _request) -> Dict:
        server.mpv.pause = True
        server.mpv.seek('00:00')
        return {'status': 'ok'}


class Server:
    def run(self, host, port, loop):
        self.mpv = MPV(ytdl=True)
        self.mpv.video = 'no'
        self.mpv.pause = True

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
        self.mpv.terminate()

    async def server_handler(self, reader, writer):
        try:
            request = await transport.read(reader)
            addr = writer.get_extra_info('peername')
            logging.info('Received %r from %r', request, addr)

            try:
                cmd = next(
                    cmd
                    for cmd in Command.subclasses
                    if cmd.name == request['msg'])
                if not cmd:
                    raise ValueError('Invalid operation')
                response = cmd.run(self, request)
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


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    Server().run(settings.HOST, settings.PORT, loop)


if __name__ == '__main__':
    main()

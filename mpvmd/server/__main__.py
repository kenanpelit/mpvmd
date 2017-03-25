import os
import logging
import asyncio
from typing import Dict, List
from mpv import MPV
from mpvmd import transport, settings
from mpvmd.server.playlist import Playlist


class State:
    def __init__(self):
        self.mpv = MPV(ytdl=True)
        self.mpv.video = 'no'
        self.mpv.pause = True
        self.playlist = Playlist()


class Command:
    subclasses: List['Command'] = []

    @property
    def name(self) -> str:
        raise NotImplementedError()

    def __init_subclass__(cls, **kwargs):
        Command.subclasses.append(cls())

    def run(self, state: State, request) -> Dict:
        raise NotImplementedError()


class PlayCommand(Command):
    name = 'play'

    def run(self, state: State, request) -> Dict:
        if 'file' in request:
            state.mpv.play(request['file'])
        state.mpv.pause = False
        return {'status': 'ok'}


class InfoCommand(Command):
    name = 'info'

    def run(self, state: State, _request) -> Dict:
        return {
            'status': 'ok',
            'paused': state.mpv.pause,
        }


class PauseCommand(Command):
    name = 'pause'

    def run(self, state: State, _request) -> Dict:
        state.mpv.pause = True
        return {'status': 'ok'}


class StopCommand(Command):
    name = 'stop'

    def run(self, state: State, _request) -> Dict:
        state.mpv.pause = True
        state.mpv.seek('00:00')
        return {'status': 'ok'}


def _get_command(name: str) -> Command:
    try:
        return next(
            cmd
            for cmd in Command.subclasses
            if cmd.name == name)
    except StopIteration:
        raise ValueError('Invalid operation')


def run(host, port, loop):
    state = State()

    async def server_handler(reader, writer):
        logging.info('Connected')
        while True:
            try:
                request = await transport.read(reader)
                if not request:
                    break
                addr = writer.get_extra_info('peername')
                logging.info('Received %r from %r', request, addr)

                try:
                    cmd = _get_command(request['msg'])
                    response = cmd.run(state, request)
                except Exception as ex:
                    response = {
                        'status': 'error',
                        'code': ex.__class__.__name__,
                        'msg': str(ex)
                    }

                logging.info('Send: %r', response)
                await transport.write(writer, response)
            except Exception as ex:
                logging.exception(ex)

        writer.close()
        logging.info('Disconnected')

    server = loop.run_until_complete(
        asyncio.start_server(server_handler, host, port, loop=loop))
    logging.info('Serving on %r', server.sockets[0].getsockname())

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    server.close()
    loop.run_until_complete(server.wait_closed())
    loop.close()
    state.mpv.terminate()


def main():
    logging.basicConfig(level=logging.INFO)
    loop = asyncio.get_event_loop()
    run(settings.HOST, settings.PORT, loop)


if __name__ == '__main__':
    main()

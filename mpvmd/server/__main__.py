import os
import logging
import asyncio
from typing import Dict, List
from mpv import MPV, MpvEventID
from mpvmd import transport, settings
from mpvmd.server.playlist import Playlist


MPV_END_FILE_REASON_EOF = 0
MPV_END_FILE_REASON_STOP = 2
MPV_END_FILE_REASON_QUIT = 3
MPV_END_FILE_REASON_ERROR = 4


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
            state.mpv.play(str(request['file']))
        elif state.playlist.current_path is None:
            state.playlist.jump_next()
            state.mpv.play(state.playlist.current_path)
        state.mpv.pause = False
        return {'status': 'ok'}


class InfoCommand(Command):
    name = 'info'

    def run(self, state: State, _request) -> Dict:
        return {
            'status': 'ok',
            'paused': state.mpv.pause,
            'random': state.playlist.random,
            'loop': state.playlist.loop,
            'volume': state.playlist.volume,
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


class PlaylistAddCommand(Command):
    name = 'playlist-add'

    def run(self, state: State, request) -> Dict:
        index = int(request['index']) if 'index' in request else None
        files = (
            [str(request['file'])]
            if 'file' in request
            else [
                str(file)
                for file in list(request['files'])
            ])

        added = 0

        def scan(dir):
            nonlocal added
            logging.info('Traversing %s', dir)
            for entry in os.scandir(dir):
                if entry.is_dir(follow_symlinks=False):
                    scan(entry.path)
                elif entry.name.lower().endswith(settings.EXTENSIONS):
                    if index is not None:
                        state.playlist.insert(entry.path, index + added)
                    else:
                        state.playlist.add(entry.path)
                    added += 1

        for file in files:
            if os.path.isdir(file):
                scan(file)
            else:
                if index is not None:
                    state.playlist.insert(file, index)
                else:
                    state.playlist.add(file)
                added += 1

        return {'status': 'ok', 'added': added}


class PlaylistRemoveCommand(Command):
    name = 'playlist-remove'

    def run(self, state: State, request) -> Dict:
        state.playlist.delete(int(request['index']))
        return {'status': 'ok'}


class PlaylistClearCommand(Command):
    name = 'playlist-clear'

    def run(self, state: State, _request) -> Dict:
        state.playlist.clear()
        return {'status': 'ok'}


class PlaylistPrevCommand(Command):
    name = 'playlist-prev'

    def run(self, state: State, _request) -> Dict:
        state.playlist.jump_prev()
        state.mpv.play(state.playlist.current_path)
        state.mpv.pause = False
        return {'status': 'ok'}


class PlaylistNextCommand(Command):
    name = 'playlist-next'

    def run(self, state: State, _request) -> Dict:
        state.playlist.jump_next()
        state.mpv.play(state.playlist.current_path)
        state.mpv.pause = False
        return {'status': 'ok'}


class PlaylistJumpCommand(Command):
    name = 'playlist-jump'

    def run(self, state: State, request) -> Dict:
        state.playlist.jump_to(int(request['index']))
        state.mpv.play(state.playlist.current_path)
        state.mpv.pause = False
        return {'status': 'ok'}


class PlaylistShuffleCommand(Command):
    name = 'shuffle'

    def run(self, state: State, request) -> Dict:
        state.playlist.shuffle()
        return {'status': 'ok'}


class ToggleRandomCommand(Command):
    name = 'random'

    def run(self, state: State, request) -> Dict:
        state.playlist.random = bool(request['random'])
        return {'status': 'ok'}


class ToggleLoopCommand(Command):
    name = 'loop'

    def run(self, state: State, request) -> Dict:
        state.playlist.loop = bool(request['loop'])
        return {'status': 'ok'}


class SetVolumeCommand(Command):
    name = 'volume'

    def run(self, state: State, request) -> Dict:
        state.mpv.volume = float(request['volume'])
        return {'status': 'ok'}


def _get_command(name: str) -> Command:
    try:
        return next(
            cmd
            for cmd in Command.subclasses
            if cmd.name == name)
    except StopIteration:
        raise ValueError('Invalid operation')


def _event_cb(state: State, event: Dict):
    if (event['event_id'] == MpvEventID.END_FILE
            and event['event']['reason'] in (
                MPV_END_FILE_REASON_EOF, MPV_END_FILE_REASON_ERROR)):
        state.playlist.jump_next()
        logging.info('Playing next file (%s)...', state.playlist.current_path)
        state.mpv.loadfile(state.playlist.current_path)
        state.mpv.pause = False


def run(host, port, loop):
    state = State()
    state.mpv.register_event_callback(lambda event: _event_cb(state, event))

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

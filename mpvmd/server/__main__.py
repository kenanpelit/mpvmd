import os
import argparse
import asyncio
import logging
import pickle
from typing import Dict, Generator, List, Optional
import mpv
from mpvmd import transport, settings, formatter
from mpvmd.server.playlist import Playlist


MPV_END_FILE_REASON_EOF = 0
MPV_END_FILE_REASON_STOP = 2
MPV_END_FILE_REASON_QUIT = 3
MPV_END_FILE_REASON_ERROR = 4


class State:
    def __init__(self):
        self.playlist = Playlist()
        self._mpv = mpv.Context(ytdl=True)
        self._mpv.set_option('video', 'no')
        self._mpv.set_option('pause', True)
        self._mpv.initialize()
        self._mpv.set_wakeup_callback(self._event_cb)

    @property
    def path(self) -> Optional[str]:
        try:
            return self._mpv.get_property('path')
        except mpv.MPVError:
            return None

    @property
    def time_pos(self) -> Optional[int]:
        try:
            return self._mpv.get_property('time-pos')
        except mpv.MPVError:
            return None

    @property
    def duration(self) -> Optional[int]:
        try:
            return self._mpv.get_property('duration')
        except mpv.MPVError:
            return None

    @property
    def metadata(self) -> Optional[Dict]:
        try:
            return self._mpv.get_property('metadata')
        except mpv.MPVError:
            return None

    @property
    def pause(self) -> bool:
        return self._mpv.get_property('pause')

    @pause.setter
    def pause(self, value: bool):
        self._mpv.set_property('pause', value)

    @property
    def volume(self) -> float:
        return self._mpv.get_property('volume')

    @volume.setter
    def volume(self, value: float):
        self._mpv.set_property('volume', value)

    def seek(self, origin: str, mode: Optional[str] = None):
        self._mpv.command('seek', origin, mode)

        def wait_for_seek() -> None:
            # XXX: super lame
            import time
            time.sleep(0.1)

        wait_for_seek()

    def play(self, file: str):
        self._mpv.command('loadfile', file)
        self.pause = False

        def wait_for_file_load() -> None:
            # XXX: super lame
            import time
            time.sleep(0.1)

        wait_for_file_load()

    def stop_playback(self) -> None:
        self._mpv.command('playlist-clear')
        self.pause = True

        def wait_for_file_end() -> None:
            # XXX: super lame
            import time
            time.sleep(0.1)

        wait_for_file_end()

    def _event_cb(self) -> None:
        while self._mpv:
            event = self._mpv.wait_event(.01)
            if event.id == mpv.Events.none:
                break

            if event.id == mpv.Events.end_file \
                    and event.data.reason in (
                        MPV_END_FILE_REASON_EOF,
                        MPV_END_FILE_REASON_ERROR):
                self._next_file()

    def _next_file(self) -> None:
        try:
            self.playlist.jump_next()
        except ValueError:
            self.stop_playback()
            logging.info('No more files to play')
            return
        logging.info('Playing next file (%s)...', self.playlist.current_path)
        self.play(self.playlist.current_path)


def _scan(dir: str) -> Generator[str, None, None]:
    logging.debug('Traversing %s', dir)
    for entry in os.scandir(dir):
        if entry.is_dir(follow_symlinks=False):
            for path in _scan(entry.path):
                yield path
        elif entry.name.lower().endswith(settings.EXTENSIONS):
            yield entry.path


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
            file = str(request['file'])
            state.play(file)
            logging.info('Playing %r', file)
        elif state.playlist.current_path is None:
            state.playlist.jump_next()
            state.play(state.playlist.current_path)
            logging.info('Starting playback: %r', state.playlist.current_path)
        else:
            state.pause = False
            logging.info('Unpausing playback')
        return {'status': 'ok'}


class InfoCommand(Command):
    name = 'info'

    def run(self, state: State, _request) -> Dict:
        return {
            'status': 'ok',
            'playlist-pos': state.playlist.current_index,
            'playlist-size': len(state.playlist),
            'paused': state.pause,
            'random': state.playlist.random,
            'loop': state.playlist.loop,
            'volume': state.volume,
            'path': state.path,
            'time-pos': state.time_pos,
            'duration': state.duration,
            'metadata': state.metadata or {},
        }


class PauseCommand(Command):
    name = 'pause'

    def run(self, state: State, _request) -> Dict:
        state.pause = True
        logging.info('Pausing playback')
        return {'status': 'ok'}


class StopCommand(Command):
    name = 'stop'

    def run(self, state: State, _request) -> Dict:
        state.stop_playback()
        logging.info('Stopping playback')
        return {'status': 'ok'}


class PlaylistInfoCommand(Command):
    name = 'playlist-info'

    def run(self, state: State, _request) -> Dict:
        return {
            'status': 'ok',
            'paths': state.playlist.items,
        }


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

        for file in files:
            if os.path.isdir(file):
                for path in sorted(_scan(file)):
                    if index is not None:
                        state.playlist.insert(path, index + added)
                    else:
                        state.playlist.add(path)
                    added += 1
            else:
                if index is not None:
                    state.playlist.insert(file, index)
                else:
                    state.playlist.add(file)
                added += 1

        logging.info('Adding %r items to the playlist', added)
        return {'status': 'ok', 'added': added}


class PlaylistRemoveCommand(Command):
    name = 'playlist-remove'

    def run(self, state: State, request) -> Dict:
        index = int(request['index'])
        state.playlist.delete(index)
        logging.info('Removing %r', index)
        return {'status': 'ok'}


class PlaylistClearCommand(Command):
    name = 'playlist-clear'

    def run(self, state: State, _request) -> Dict:
        state.playlist.clear()
        logging.info('Clearing the playlist')
        return {'status': 'ok'}


class PlaylistPrevCommand(Command):
    name = 'playlist-prev'

    def run(self, state: State, _request) -> Dict:
        state.playlist.jump_prev()
        state.play(state.playlist.current_path)
        logging.info(
            'Jumping to %r: %r',
            state.playlist.current_index,
            state.playlist.current_path)
        return {'status': 'ok'}


class PlaylistNextCommand(Command):
    name = 'playlist-next'

    def run(self, state: State, _request) -> Dict:
        state.playlist.jump_next()
        state.play(state.playlist.current_path)
        logging.info(
            'Jumping to %r: %r',
            state.playlist.current_index,
            state.playlist.current_path)
        return {'status': 'ok'}


class PlaylistJumpCommand(Command):
    name = 'playlist-jump'

    def run(self, state: State, request) -> Dict:
        state.playlist.jump_to(int(request['index']))
        state.play(state.playlist.current_path)
        logging.info(
            'Jumping to %r: %r',
            state.playlist.current_index,
            state.playlist.current_path)
        return {'status': 'ok'}


class PlaylistShuffleCommand(Command):
    name = 'shuffle'

    def run(self, state: State, request) -> Dict:
        state.playlist.shuffle()
        logging.info('Shuffling the playlist')
        return {'status': 'ok'}


class ToggleRandomCommand(Command):
    name = 'random'

    def run(self, state: State, request) -> Dict:
        state.playlist.random = bool(request['random'])
        logging.info('Setting random flag to %r', state.playlist.random)
        return {'status': 'ok'}


class ToggleLoopCommand(Command):
    name = 'loop'

    def run(self, state: State, request) -> Dict:
        state.playlist.loop = bool(request['loop'])
        logging.info('Setting loop flag to %r', state.playlist.loop)
        return {'status': 'ok'}


class SetVolumeCommand(Command):
    name = 'volume'

    def run(self, state: State, request) -> Dict:
        state.volume = float(request['volume'])
        logging.info('Setting volume to %r', state.volume)
        return {'status': 'ok'}


class SeekCommand(Command):
    name = 'seek'

    def run(self, state: State, request) -> Dict:
        where = str(request['where'])
        value, mode = formatter.parse_seek(where)
        state.seek(str(value), mode)
        logging.info(
            'Seeking to %r',
            formatter.format_duration(state.time_pos)
            or '-')
        return {'status': 'ok'}


def _get_command(name: str) -> Command:
    try:
        return next(
            cmd
            for cmd in Command.subclasses
            if cmd.name == name)
    except StopIteration:
        raise ValueError('Invalid operation')


def load_db(state: State, path: str):
    if not os.path.exists(path):
        return
    try:
        with open(path, 'rb') as handle:
            obj = pickle.load(handle)
            state.playlist.items = obj['playlist']
            if obj['index'] is not None:
                state.playlist.jump_to(obj['index'])
            state.playlist.random = obj['random']
            state.playlist.loop = obj['loop']
            state.volume = obj['volume']
            if obj['playback']['path'] is not None:
                state.play(obj['playback']['path'])
                state.pause = obj['playback']['pause']
                state.seek(obj['playback']['pos'], 'absolute')
    except Exception as error:
        logging.exception(error)
        return


def store_db(state: State, path: str):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, 'wb') as handle:
        pickle.dump({
            'playlist': state.playlist.items,
            'index': state.playlist.current_index,
            'random': state.playlist.random,
            'loop': state.playlist.loop,
            'volume': state.volume,
            'playback': {
                'path': state.path,
                'pos': state.time_pos,
                'pause': state.pause,
            },
        }, handle)


def run(host, port, loop, db_path):
    state = State()
    load_db(state, db_path)

    async def server_handler(reader, writer):
        addr = writer.get_extra_info('peername')
        logging.debug('%r: connected', addr)
        while True:
            try:
                request = await transport.read(reader)
                if not request:
                    break
                logging.debug('%r: receive %r', addr, request)

                try:
                    cmd = _get_command(request['msg'])
                    response = cmd.run(state, request)
                except Exception as ex:
                    response = {
                        'status': 'error',
                        'code': ex.__class__.__name__,
                        'msg': str(ex)
                    }

                logging.debug('%r: send %r', addr, response)
                await transport.write(writer, response)
            except (ConnectionResetError, BrokenPipeError) as ex:
                logging.exception(ex)
                break
            except Exception as ex:
                logging.exception(ex)

        writer.close()
        logging.debug('%r: disconnected', addr)

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
    store_db(state, db_path)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='MPV music daemon client')
    parser.add_argument('--host', default=settings.HOST)
    parser.add_argument('-p', '--port', type=int, default=settings.PORT)
    parser.add_argument(
        '--db-path', type=str, default='~/.local/share/mpvmd/db.dat')
    parser.add_argument('-d', '--debug', action='store_true')
    return parser.parse_args()


def main():
    args = parse_args()
    host: str = args.host
    port: int = args.port
    db_path: str = os.path.expanduser(args.db_path)
    debug: bool = args.debug

    logging.basicConfig(level=logging.DEBUG if debug else logging.INFO)
    loop = asyncio.get_event_loop()
    run(host, port, loop, db_path)


if __name__ == '__main__':
    main()

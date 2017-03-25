import argparse
import asyncio
from typing import Optional, Dict, List
from mpvmd import transport, settings


class ApiError(RuntimeError):
    def __init__(self, code: str, text: str) -> None:
        super().__init__('API error ({}: {})'.format(code, text))
        self.code = code
        self.text = text


def assert_status(response: Dict) -> None:
    if response['status'] != 'ok':
        raise ApiError(response['code'], response['msg'])


async def show_info(reader, writer) -> None:
    await transport.write(writer, {'msg': 'info'})
    info = await transport.read(reader)
    metadata = {
        key.lower(): value
        for key, value in (info['metadata'] or {}).items()
    }

    print('({}/{}) {}'.format(
        '-' if info['playlist-pos'] is None else info['playlist-pos'],
        info['playlist-size'] or '-',
        info['path'] or '-'))
    print('Artist: {}'.format(metadata.get('artist') or '?'))
    print('Date:   {}'.format(metadata.get('date') or '?'))
    print('Title:  {}'.format(metadata.get('title') or '?'))
    print()
    print('Pause:  {}'.format(info['paused']))
    print('Loop:   {}'.format(info['loop']))
    print('Random: {}'.format(info['random']))
    print('Volume: {}'.format(info['volume']))
    print()


class Command:
    names: List[str] = []
    subclasses: List['Command'] = []

    def __init_subclass__(cls, **kwargs):
        Command.subclasses.append(cls())

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        pass

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        raise NotImplementedError()


class PlayCommand(Command):
    names = ['play']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('file', nargs='?')

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        file: Optional[str] = args.file
        request = {'msg': 'play'}
        if file:
            request['file'] = args.file
        await transport.write(writer, request)
        assert_status(await transport.read(reader))


class PlayPauseCommand(Command):
    names = ['play-pause']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'info'})
        info = await transport.read(reader)
        if info['paused']:
            await transport.write(writer, {'msg': 'play'})
        else:
            await transport.write(writer, {'msg': 'pause'})
        assert_status(await transport.read(reader))


class PauseCommand(Command):
    names = ['pause']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'pause'})
        assert_status(await transport.read(reader))


class StopCommand(Command):
    names = ['stop']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'stop'})
        assert_status(await transport.read(reader))


class PlaylistAddCommand(Command):
    names = ['add']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('file', nargs='+')
        parser.add_argument('-i', '--index', type=int)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        files: List[str] = args.file
        index: Optional[int] = args.index
        request = {'msg': 'playlist-add', 'files': files}
        if index is not None:
            request['index'] = index
        await transport.write(writer, request)
        assert_status(await transport.read(reader))


class PlaylistDeleteCommand(Command):
    names = ['del', 'delete']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('index', type=int)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        index: int = args.index
        await transport.write(
            writer, {'msg': 'playlist-remove', 'index': index})
        assert_status(await transport.read(reader))


class PlaylistClearCommand(Command):
    names = ['clear']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-clear'})
        assert_status(await transport.read(reader))


class PlaylistPrevCommand(Command):
    names = ['prev']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-prev'})
        assert_status(await transport.read(reader))


class PlaylistNextCommand(Command):
    names = ['next']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-next'})
        assert_status(await transport.read(reader))


class PlaylistJumpCommand(Command):
    names = ['jump']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('index', type=int)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        index: int = args.index
        await transport.write(writer, {'msg': 'playlist-jump', 'index': index})
        assert_status(await transport.read(reader))


class PlaylistShuffleCommand(Command):
    names = ['shuffle']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-shuffle'})
        assert_status(await transport.read(reader))


class ToggleRandomCommand(Command):
    names = ['toggle-random']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'info'})
        info = await transport.read(reader)
        await transport.write(
            writer, {'msg': 'random', 'random': not info['random']})
        assert_status(await transport.read(reader))


class ToggleLoopCommand(Command):
    names = ['toggle-loop']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'info'})
        info = await transport.read(reader)
        await transport.write(
            writer, {'msg': 'loop', 'loop': not info['loop']})
        assert_status(await transport.read(reader))


class SetVolumeCommand(Command):
    names = ['vol', 'volume']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        def check_volume(value):
            volume = float(value)
            if volume < 0 or volume > 200.0:
                raise argparse.ArgumentTypeError(
                    'Volume must be within 0-200 range')
            return volume

        parser.add_argument('volume', type=check_volume)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        volume: float = args.volume
        await transport.write(writer, {'msg': 'volume', 'volume': volume})
        assert_status(await transport.read(reader))


def parse_args() -> Optional[argparse.Namespace]:
    parser = argparse.ArgumentParser(description='MPV music daemon client')
    parser.set_defaults(run=None)
    parser.add_argument('--host', default=settings.HOST)
    parser.add_argument('-p', '--port', type=int, default=settings.PORT)
    subparsers = parser.add_subparsers(help='choose the command', dest='cmd')
    for command in Command.subclasses:
        subparser = subparsers.add_parser(
            command.names[0],
            aliases=command.names[1:])
        command.decorate_arg_parser(subparser)
        subparser.set_defaults(run=command.run)
    return parser.parse_args()


async def run(loop):
    args = parse_args()
    host: str = args.host
    port: int = args.port
    reader, writer = await asyncio.open_connection(host, port, loop=loop)
    if args.run:
        await args.run(args, reader, writer)
    await show_info(reader, writer)
    writer.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()


if __name__ == '__main__':
    main()

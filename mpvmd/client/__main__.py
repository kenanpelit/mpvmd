import argparse
import asyncio
import sys
from typing import Optional, List
from mpvmd import transport, settings


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
        print(await transport.read(reader))


class PlayPauseCommand(Command):
    names = ['play-pause']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'info'})
        info = await transport.read(reader)
        if info['paused']:
            await transport.write(writer, {'msg': 'play'})
        else:
            await transport.write(writer, {'msg': 'pause'})
        print(await transport.read(reader))


class PauseCommand(Command):
    names = ['pause']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'pause'})
        print(await transport.read(reader))


class StopCommand(Command):
    names = ['stop']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'stop'})
        print(await transport.read(reader))


class PlaylistAddCommand(Command):
    names = ['add']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('file')
        parser.add_argument('-i', '--index', type=int)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        file: str = args.file
        index: Optional[int] = args.index
        request = {'msg': 'playlist-add', 'file': file}
        if index is not None:
            request['index'] = index
        await transport.write(writer, request)
        print(await transport.read(reader))


class PlaylistDeleteCommand(Command):
    names = ['del', 'delete']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('index', type=int)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        index: int = args.index
        await transport.write(
            writer, {'msg': 'playlist-remove', 'index': index})
        print(await transport.read(reader))


class PlaylistClearCommand(Command):
    names = ['clear']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-clear'})
        print(await transport.read(reader))


class PlaylistPrevCommand(Command):
    names = ['prev']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-prev'})
        print(await transport.read(reader))


class PlaylistNextCommand(Command):
    names = ['next']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-next'})
        print(await transport.read(reader))


class PlaylistJumpCommand(Command):
    names = ['jump']

    def decorate_arg_parser(self, parser: argparse.ArgumentParser) -> None:
        parser.add_argument('index', type=int)

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        index: int = args.index
        await transport.write(writer, {'msg': 'playlist-jump', 'index': index})
        print(await transport.read(reader))


class PlaylistShuffleCommand(Command):
    names = ['shuffle']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'playlist-shuffle'})
        print(await transport.read(reader))


class ToggleRandomCommand(Command):
    names = ['toggle-random']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'info'})
        info = await transport.read(reader)
        await transport.write(
            writer, {'msg': 'random', 'random': not info['random']})
        print(await transport.read(reader))


class ToggleLoopCommand(Command):
    names = ['toggle-loop']

    async def run(self, args: argparse.Namespace, reader, writer) -> None:
        await transport.write(writer, {'msg': 'info'})
        info = await transport.read(reader)
        await transport.write(
            writer, {'msg': 'loop', 'loop': not info['loop']})
        print(await transport.read(reader))


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
        print(await transport.read(reader))


def parse_args() -> Optional[argparse.Namespace]:
    parser = argparse.ArgumentParser(description='MPV music daemon client')
    subparsers = parser.add_subparsers(help='choose the command', dest='cmd')
    for command in Command.subclasses:
        subparser = subparsers.add_parser(
            command.names[0],
            aliases=command.names[1:])
        command.decorate_arg_parser(subparser)
        subparser.set_defaults(run=command.run)
    args = parser.parse_args()
    if not args.run:
        parser.print_help()
        return None
    return args


async def run(loop):
    args = parse_args()
    if not args:
        sys.exit(1)
    reader, writer = await asyncio.open_connection(
        settings.HOST, settings.PORT, loop=loop)
    await args.run(args, reader, writer)
    writer.close()


def main():
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(loop))
    loop.close()


if __name__ == '__main__':
    main()

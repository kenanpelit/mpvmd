import random
from typing import Optional, List


class Randomizer:
    def __init__(self, value_factory):
        self.list = []
        self.pos = None
        self._get_value = value_factory

    def next(self) -> int:
        return self._jump(1)

    def prev(self) -> int:
        return self._jump(-1)

    def _jump(self, delta: int) -> int:
        if self.pos is None:
            self.list = [self._get_value()]
            self.pos = 0
            return self.list[0]

        self.pos += delta
        if self.pos >= 0 and self.pos < len(self.list):
            return self.list[self.pos]

        ret = self._get_value()
        if self.pos == -1:
            self.pos = 0
            self.list.insert(0, ret)
            return ret
        if self.pos == len(self.list):
            self.list.append(ret)
            return ret


class Playlist:
    def __init__(self) -> None:
        self.random = False
        self.loop = False
        self.items: List[str] = []
        self.current_index: Optional[int] = None
        self._deleted: Optional[str] = None
        self._randomizer = Randomizer(self._get_random_track_number)

    @property
    def current_path(self) -> Optional[str]:
        if self._deleted:
            return self._deleted
        if self.current_index is None:
            return None
        return self.items[self.current_index]

    def __len__(self) -> int:
        return len(self.items)

    def add(self, path: str) -> None:
        self.items.append(path)

    def insert(self, path: str, index: int) -> None:
        if index < 0 or index > len(self.items):
            raise IndexError('Playlist index out of bounds')
        self.items.insert(index, path)

    def delete(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            raise IndexError('Playlist index out of bounds')
        current_path = self.current_path
        self.items.pop(index)
        if self.current_index is None:
            return
        if not self.items:
            self.current_index = None
        if index == self.current_index:
            self._deleted = current_path
        elif index < self.current_index:
            self.current_index -= 1

    def clear(self) -> None:
        self.items = []
        self.current_index = None

    def jump_prev(self) -> None:
        self.current_index = self._jump_relative(-1)

    def jump_next(self) -> None:
        self.current_index = self._jump_relative(1)

    def jump_to(self, index: int) -> None:
        if index < 0 or index >= len(self.items):
            raise IndexError('Playlist index out of bounds')
        self.current_index = index
        self._deleted = None

    def shuffle(self) -> None:
        random.shuffle(self.items)
        self.current_index = None

    def _jump_relative(self, delta: int) -> int:
        if not self.items:
            raise ValueError('Playlist is empty')

        if self.random:
            if delta < 0:
                return self._randomizer.prev()
            return self._randomizer.next()
        elif self.current_index is None:
            if delta < 0:
                ret = len(self.items) - 1
            else:
                ret = 0
        elif self._deleted:
            self._deleted = None
            if delta < 0:
                ret = self.current_index - 1
            else:
                ret = self.current_index
        else:
            ret = self.current_index + delta
        return ret % len(self.items)

    def _get_random_track_number(self):
        return random.randint(0, len(self.items) - 1)

from typing import Optional, List


class Playlist:
    def __init__(self) -> None:
        self.items: List[str] = []
        self.current_index: Optional[int] = None
        self._deleted: Optional[str] = None

    @property
    def current_path(self) -> Optional[str]:
        if self._deleted:
            return self._deleted
        if self.current_index is None:
            return None
        return self.items[self.current_index]

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

    def _jump_relative(self, delta: int) -> int:
        if not self.items:
            raise ValueError('Playlist is empty')

        if self.current_index is None:
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

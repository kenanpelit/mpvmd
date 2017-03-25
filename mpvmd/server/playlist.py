from typing import Optional, List


class Playlist:
    def __init__(self) -> None:
        self.items: List[str] = []
        self.current_index: Optional[int] = None

    @property
    def current_path(self) -> Optional[str]:
        if self.current_index is None:
            return None
        return self.items[self.current_index]

    def add(self, path: str) -> None:
        self.items.append(path)

    def jump_prev(self) -> None:
        self.current_index = self._jump_relative(-1)

    def jump_next(self) -> None:
        self.current_index = self._jump_relative(1)

    def _jump_relative(self, delta: int) -> int:
        if not self.items:
            raise ValueError('Playlist is empty')

        if self.current_index is None:
            if delta < 0:
                ret = len(self.items) - 1
            else:
                ret = 0
        else:
            ret = self.current_index + delta
        return ret % len(self.items)

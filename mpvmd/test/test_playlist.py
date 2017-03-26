from mpvmd.server.playlist import Playlist, Randomizer


def test_randomizer():
    index = 0

    def value_factory():
        nonlocal index
        index += 1
        return index

    randomizer = Randomizer(value_factory)
    assert randomizer.next() == 1
    assert randomizer.prev() == 2
    assert randomizer.next() == 1
    assert randomizer.next() == 3
    assert randomizer.prev() == 1
    assert randomizer.prev() == 2
    assert randomizer.prev() == 4


def test_prev():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    assert playlist.current_path is None
    playlist.jump_prev()
    assert playlist.current_path == '456'
    playlist.jump_prev()
    assert playlist.current_path == '123'
    playlist.jump_prev()
    assert playlist.current_path == '456'


def test_next():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    assert playlist.current_path is None
    playlist.jump_next()
    assert playlist.current_path == '123'
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.jump_next()
    assert playlist.current_path == '123'


def test_delete_prev_when_none_playing():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    assert playlist.current_path is None
    playlist.delete(0)
    playlist.jump_prev()
    assert playlist.current_path == '456'
    playlist.jump_prev()
    assert playlist.current_path == '456'


def test_delete_next_when_none_playing():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    assert playlist.current_path is None
    playlist.delete(0)
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.jump_next()
    assert playlist.current_path == '456'


def test_delete_prev_when_playing_earlier():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    playlist.add('789')
    playlist.jump_next()
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.delete(0)
    assert playlist.current_path == '456'
    playlist.jump_prev()
    assert playlist.current_path == '789'
    playlist.jump_prev()
    assert playlist.current_path == '456'


def test_delete_next_when_playing_earlier():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    playlist.add('789')
    playlist.jump_next()
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.delete(0)
    assert playlist.current_path == '456'
    playlist.jump_next()
    assert playlist.current_path == '789'
    playlist.jump_next()
    assert playlist.current_path == '456'


def test_delete_prev_when_playing_later():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    playlist.add('789')
    playlist.jump_next()
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.delete(2)
    assert playlist.current_path == '456'
    playlist.jump_prev()
    assert playlist.current_path == '123'
    playlist.jump_prev()
    assert playlist.current_path == '456'


def test_delete_next_when_playing_later():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    playlist.add('789')
    playlist.jump_next()
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.delete(2)
    assert playlist.current_path == '456'
    playlist.jump_next()
    assert playlist.current_path == '123'
    playlist.jump_next()
    assert playlist.current_path == '456'


def test_delete_prev_when_playing_deleted():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    playlist.add('789')
    playlist.jump_next()
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.delete(1)
    assert playlist.current_path == '456'
    playlist.jump_prev()
    assert playlist.current_path == '123'
    playlist.jump_prev()
    assert playlist.current_path == '789'


def test_delete_next_when_playing_deleted():
    playlist = Playlist()
    playlist.add('123')
    playlist.add('456')
    playlist.add('789')
    playlist.jump_next()
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.delete(1)
    assert playlist.current_path == '456'
    playlist.jump_next()
    assert playlist.current_path == '789'
    playlist.jump_next()
    assert playlist.current_path == '123'

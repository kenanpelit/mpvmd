from mpvmd.server.playlist import Playlist


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
    playlist.jump_next()
    assert playlist.current_path == '456'
    playlist.jump_next()
    assert playlist.current_path == '123'

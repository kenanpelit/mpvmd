mpvmd
=====

Client-server CLI music player based on
[`libmpv`](https://github.com/mpv-player/mpv) and [suckless
philosophy](http://suckless.org/philosophy),
meant as an alternative to `mpd`+`mpc`.

## Quick start

```console
$ git clone https://github.com/rr-/mpvmd
$ cd mpvmd
$ pip install --user --upgrade .
$ mpvmd &>/dev/null &; disown
$ mpvmc play somefile.mp3
```

To persist across reboots, see [Installing the daemon as systemd
unit](#installing-the-daemon-as-systemd-unit).

## Features

- Headless daemon
- CLI client, usable in panels, hotkeys etc.
- Hackable (written in modern Python and code is kept to minimum)
- Single playlist
    - Adding a file, URL, or directory tree
    - Listing paths (use `grep` to filter)
    - Shuffling
    - Clearing
    - Deleting a single track
    - Playing single files "off the playlist"
- Convenient seeking (percentage, absolute, relative)
- Showing info about currently playing track
- Very basic title formatting (inspired by `mpc`'s `--format`)
- Random playback (keeps the history)
- Looping a single track
- Volume control
- Resuming playback and keeping the playlist between daemon restarts

## Miscellaneous

#### Compiling `libmpv` (if you can't install it your with package manager)

```console
$ git clone https://github.com/mpv-player/mpv
$ cd mpv
$ ./waf configure --enable-libmpv
$ ./waf
$ sudo ./waf install
```

#### Installing the daemon as systemd unit

```console
$ vim ~/.config/systemd/user/mpvmd.service
```

```
[Unit]
Description=mpvmd
After=syslog.target network.target

[Service]
Type=simple
ExecStart=/usr/bin/python3 /home/YOUR_USERNAME/.local/bin/mpvmd
Environment=LD_LIBRARY_PATH=/usr/local/lib
Restart=on-abort
KillSignal=SIGINT

[Install]
WantedBy=multi-user.target
```

```console
$ systemctl enable --user mpvmd
$ systemctl start --user mpvmd
```

#### Bug reports, new features

Report both here on GitHub.

#### Why not just `mpd`?

`mpd` works exceptionally slow with big playlists, often resulting in `mpd
error: Connection refused`. Also [the list of its
dependencies](https://www.archlinux.org/packages/extra/i686/mpd/) is quite
long.

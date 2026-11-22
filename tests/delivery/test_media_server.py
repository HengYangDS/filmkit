"""Ranged media serving."""

import os
import subprocess
import sys
import threading
from functools import partial
from http.server import ThreadingHTTPServer
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

import filmkit.delivery.media_server as delivery_media_server


def test_media_ranges_support_seek_and_reject_unsatisfied_range(tmp_path):
    (tmp_path / "film.bin").write_bytes(b"0123456789abcdef")
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(delivery_media_server.MediaHandler, directory=str(tmp_path))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_port}/film.bin"
    try:
        with urlopen(Request(url, headers={"Range": "bytes=4-7"}), timeout=5) as response:
            assert response.status == 206
            assert response.read() == b"4567"
            assert response.headers["Content-Range"] == "bytes 4-7/16"
        with pytest.raises(HTTPError) as error:
            urlopen(Request(url, headers={"Range": "bytes=50-"}), timeout=5)
        with error.value:
            assert error.value.code == 416
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def test_the_server_loads_the_film_s_declaration_when_it_starts(tmp_path):
    # It serves a film's built media, which only a film whose declaration loads can build: a
    # declaration that does not load stops it before it serves, with the declaration named.
    (tmp_path / "content").mkdir()
    (tmp_path / "content/film.toml").write_text('title = "no film"\n')
    media = tmp_path / "media"
    media.mkdir()
    command = [sys.executable, "-B", "-m", "filmkit.delivery.media_server", "--directory"]
    started = subprocess.run(
        [*command, str(media), "--port", "0"],
        env={**os.environ, "FILMKIT_ROOT": str(tmp_path)},
        capture_output=True,
        text=True,
        timeout=10,
        check=False,
    )
    assert started.returncode == 1
    assert "FilmError: content/film.toml is not a film declaration" in started.stderr
    assert started.stdout == ""

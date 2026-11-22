"""Ranged media serving."""

import os
import select
import socket
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


def test_the_server_serves_a_film_s_built_media_without_loading_its_declaration(tmp_path):
    # The server serves files and reads no declaration: a film whose declaration does not load
    # still has its built media served, from the films' folder unless another is named.
    (tmp_path / "content").mkdir()
    (tmp_path / "content/film.toml").write_text('title = "no film"\n')
    films = tmp_path / "build/artifacts/film"
    films.mkdir(parents=True)
    (films / "film.bin").write_bytes(b"0123456789")
    with socket.socket() as probe:
        probe.bind(("127.0.0.1", 0))
        port = probe.getsockname()[1]
    server = subprocess.Popen(
        [sys.executable, "-B", "-m", "filmkit.delivery.media_server", "--port", str(port)],
        env={**os.environ, "FILMKIT_ROOT": str(tmp_path)},
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )
    try:
        assert select.select([server.stdout], [], [], 10)[0], "the server printed nothing"
        started = server.stdout.readline()
        assert started == f"Serving review media at http://127.0.0.1:{port}/\n", started
        with urlopen(f"http://127.0.0.1:{port}/film.bin", timeout=5) as response:
            assert response.read() == b"0123456789"
    finally:
        server.terminate()
        server.communicate(timeout=10)

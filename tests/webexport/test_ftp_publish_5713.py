"""Az FTP-közzététel minden webexport-fájlt a fiók gyökerébe visz (#5713)."""

# rontás-kontroll: FtpPublisher.upload = 0 → 1 failed

from __future__ import annotations

import ftplib
import posixpath
import socket
import threading

import pytest

from picasapy.index import PhotoRecord
from picasapy.webexport import AlbumExportData, WebExportSettings, list_templates, run_web_export
from picasapy.webexport import ftp_publish
from picasapy.webexport.images import prepare_photo_exports
from picasapy.webexport.ftp_publish import FtpAccount, FtpPublisher
from picasapy.webexport.sizes import (
    DEFAULT_SIZE_INDEX,
    image_size_for_index,
    settings_for_template,
)
from support.jpeg_factory import make_jpeg


class _LocalFtpServer:
    """Kis, csak a szükséges FTP-parancsokat beszélő helyi tesztkiszolgáló."""

    def __init__(self):
        self.root = {"/", "/gallery"}
        self.files: dict[str, bytes] = {}
        self._listener = socket.socket()
        self._listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._listener.bind(("127.0.0.1", 0))
        self._listener.listen(1)
        self._listener.settimeout(5)
        self.host, self.port = self._listener.getsockname()
        self._thread = threading.Thread(target=self._serve, daemon=True)
        self._error: BaseException | None = None

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *_exc):
        self._listener.close()
        self._thread.join(timeout=5)
        if self._thread.is_alive():
            raise AssertionError("a helyi FTP-kiszolgáló nem állt le")
        if self._error is not None:
            raise self._error

    @staticmethod
    def _write(connection, message: str) -> None:
        connection.sendall((message + "\r\n").encode("ascii"))

    @staticmethod
    def _path(cwd: str, name: str) -> str:
        return posixpath.normpath(posixpath.join(cwd, name))

    def _serve(self):
        try:
            control, _address = self._listener.accept()
            with control:
                control.settimeout(5)
                self._write(control, "220 local test FTP")
                buffer = b""
                cwd = "/"
                data_listener = None
                while True:
                    while b"\n" not in buffer:
                        chunk = control.recv(4096)
                        if not chunk:
                            return
                        buffer += chunk
                    raw, buffer = buffer.split(b"\n", 1)
                    command, _, argument = raw.decode("utf-8").strip().partition(" ")
                    command = command.upper()
                    argument = argument.strip()
                    if command == "USER":
                        self._write(control, "331 password required")
                    elif command == "PASS":
                        self._write(control, "230 logged in")
                    elif command == "TYPE":
                        self._write(control, "200 binary")
                    elif command == "PWD":
                        self._write(control, f'257 "{cwd}"')
                    elif command == "CWD":
                        target = self._path(cwd, argument)
                        if target in self.root:
                            cwd = target
                            self._write(control, "250 directory changed")
                        else:
                            self._write(control, "550 no such directory")
                    elif command == "MKD":
                        target = self._path(cwd, argument)
                        self.root.add(target)
                        self._write(control, f'257 "{target}" created')
                    elif command == "PASV":
                        data_listener = socket.socket()
                        data_listener.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                        data_listener.bind(("127.0.0.1", 0))
                        data_listener.listen(1)
                        port = data_listener.getsockname()[1]
                        self._write(
                            control,
                            f"227 Entering Passive Mode (127,0,0,1,{port // 256},{port % 256})",
                        )
                    elif command == "STOR":
                        if data_listener is None:
                            self._write(control, "425 passive connection missing")
                            continue
                        self._write(control, "150 opening data connection")
                        data_listener.settimeout(5)
                        data, _address = data_listener.accept()
                        with data:
                            chunks = []
                            while chunk := data.recv(65536):
                                chunks.append(chunk)
                        data_listener.close()
                        data_listener = None
                        self.files[self._path(cwd, argument)] = b"".join(chunks)
                        self._write(control, "226 transfer complete")
                    elif command == "QUIT":
                        self._write(control, "221 goodbye")
                        return
                    else:
                        self._write(control, "200 ok")
        except BaseException as error:  # a tesztben a szál hibája is legyen látható
            self._error = error


class _MemoryFtp:
    """FTP-protokollhelyettesítő a socket nélküli feltöltési próbához."""

    def __init__(self):
        self.directories = {"/"}
        self.files: dict[str, bytes] = {}
        self.current = "/"

    def __enter__(self):
        return self

    def __exit__(self, *_exc):
        return None

    def connect(self, *_args):
        return None

    def login(self, *_args):
        return None

    def _resolve(self, path: str) -> str:
        return posixpath.normpath(
            path if path.startswith("/") else posixpath.join(self.current, path)
        )

    def cwd(self, path: str):
        target = self._resolve(path)
        if target not in self.directories:
            raise ftplib.error_perm("550 no such directory")
        self.current = target

    def mkd(self, path: str):
        self.directories.add(self._resolve(path))

    def storbinary(self, command: str, data):
        name = command.partition(" ")[2]
        self.files[self._resolve(name)] = data.read()


def test_a_teljes_webexport_fajlfa_feltoltodik_a_fiok_gyokerere(tmp_path):
    source = tmp_path / "forras"
    source.mkdir()
    image = source / "valodi-kep.jpg"
    make_jpeg(image, size=(80, 60))
    photo = PhotoRecord(
        id=1,
        folder_path=str(source),
        name=image.name,
        kind="photo",
        size=image.stat().st_size,
        mtime_ns=0,
        star=False,
        caption="Tesztkép",
        keywords=None,
        rotate_steps=0,
        filters=None,
        taken_at=None,
        orientation=1,
        width=80,
        height=60,
    )
    template = next(item for item in list_templates() if item.id == "feher")
    settings = settings_for_template(
        template.path,
        image_size_for_index(DEFAULT_SIZE_INDEX),
        WebExportSettings(),
    )
    export = tmp_path / "export"
    image_report = prepare_photo_exports((photo,), export, settings)
    assert image_report.photos
    report = run_web_export(
        template.path,
        export,
        AlbumExportData(name="Valódi fénykép", photos=image_report.photos),
        settings,
    )
    assert report.output_files
    helyi = {
        path.relative_to(export).as_posix(): path.read_bytes()
        for path in export.rglob("*")
        if path.is_file()
    }

    try:
        server = _LocalFtpServer()
    except OSError as error:
        pytest.skip(f"a homokozó nem enged helyi FTP-socketet: {error}")

    with server:
        account = FtpAccount(
            account_id="teszt-fiok",
            name="Teszt FTP",
            domain=server.host,
            user="galeria",
            root="/gallery",
        )
        count = FtpPublisher(port=server.port).upload(export, account, "titok")

    assert count == len(helyi)
    assert {
        path.removeprefix("/gallery/"): data for path, data in server.files.items()
    } == helyi


def test_a_feltolto_a_beagyazott_fajlokat_is_atviszi_socket_nelkul(
    tmp_path, monkeypatch
):
    source = tmp_path / "export"
    (source / "kepek" / "album").mkdir(parents=True)
    (source / "index.html").write_bytes(b"<h1>album</h1>")
    (source / "kepek" / "album" / "kep.jpg").write_bytes(b"jpeg-adat")
    server = _MemoryFtp()
    monkeypatch.setattr(ftp_publish, "_FTP", lambda timeout: server)

    count = FtpPublisher().upload(
        source,
        FtpAccount("id", "Teszt", "ftp.example.test", "user", "/gallery"),
        "titok",
    )

    assert count == 2
    assert server.files == {
        "/gallery/index.html": b"<h1>album</h1>",
        "/gallery/kepek/album/kep.jpg": b"jpeg-adat",
    }

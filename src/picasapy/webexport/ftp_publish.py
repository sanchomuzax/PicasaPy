"""FTP-fiókok és a webexport fájljainak feltöltése (#5713)."""

from __future__ import annotations

import ftplib
import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol

_FTP = ftplib.FTP


class _Settings(Protocol):
    def value(self, key: str, default=None): ...

    def setValue(self, key: str, value) -> None: ...

    def remove(self, key: str) -> None: ...


class _SecretStore(Protocol):
    def get_password(self, service: str, account: str) -> str | None: ...

    def set_password(self, service: str, account: str, password: str) -> None: ...

    def delete_password(self, service: str, account: str) -> None: ...


class SystemKeyring:
    """A platform rendszer-kulcstárát használja, és nem esik vissza fájlra."""

    @staticmethod
    def _keyring():
        try:
            import keyring
        except ImportError as error:  # csomagolási hiba esetén is maradjon biztonságos
            raise RuntimeError(
                "The system key store is unavailable."
            ) from error
        return keyring

    def get_password(self, service: str, account: str) -> str | None:
        return self._keyring().get_password(service, account)

    def set_password(self, service: str, account: str, password: str) -> None:
        self._keyring().set_password(service, account, password)

    def delete_password(self, service: str, account: str) -> None:
        try:
            self._keyring().delete_password(service, account)
        except self._keyring().errors.PasswordDeleteError:
            pass


@dataclass(frozen=True)
class FtpAccount:
    """Az FTP-fiók nyilvános adatai; jelszót szándékosan nem tartalmaz."""

    account_id: str
    name: str
    domain: str
    user: str
    root: str


class FtpAccountStore:
    """A fiók leíróit QSettingsben, a jelszót a rendszer-kulcstárban tartja."""

    SERVICE = "PicasaPy FTP"
    ACCOUNTS_KEY = "webexport/ftpAccounts"
    SELECTED_KEY = "webexport/selectedFtpAccount"

    def __init__(self, settings: _Settings, secrets: _SecretStore | None = None):
        self._settings = settings
        self._secrets = secrets or SystemKeyring()

    def list_accounts(self) -> tuple[FtpAccount, ...]:
        raw = self._settings.value(self.ACCOUNTS_KEY, "[]")
        try:
            records = json.loads(raw) if isinstance(raw, str) else raw
        except (TypeError, json.JSONDecodeError):
            records = []
        accounts = []
        for record in records if isinstance(records, list) else []:
            try:
                accounts.append(FtpAccount(**record))
            except (TypeError, ValueError):
                continue
        return tuple(accounts)

    def save_account(
        self,
        *,
        account_id: str,
        name: str,
        domain: str,
        user: str,
        root: str,
        password: str,
    ) -> FtpAccount:
        name, domain, user = name.strip(), domain.strip(), user.strip()
        root = root.strip() or "/"
        if not all((name, domain, user)):
            raise ValueError("The account name, server, and user name are required.")
        if any(char in value for value in (name, domain, user, root, password) for char in "\r\n"):
            raise ValueError("FTP account fields cannot contain line breaks.")
        existing = next(
            (item for item in self.list_accounts() if item.account_id == account_id),
            None,
        ) if account_id else None
        identity = existing.account_id if existing else uuid.uuid4().hex
        if not existing and not password:
            raise ValueError("A password is required for a new account.")
        previous_password = self.password_for(identity) if existing else None
        if existing and not password and not previous_password:
            raise ValueError("The saved FTP password is missing.")

        account = FtpAccount(identity, name, domain, user, root)
        old_accounts = self.list_accounts()
        try:
            if password:
                self._secrets.set_password(self.SERVICE, identity, password)
            new_accounts = [
                item for item in old_accounts if item.account_id != identity
            ]
            new_accounts.append(account)
            self._write_accounts(new_accounts)
        except Exception:
            if existing and password and previous_password:
                self._secrets.set_password(self.SERVICE, identity, previous_password)
            elif not existing and password:
                self._secrets.delete_password(self.SERVICE, identity)
            raise
        return account

    def delete_account(self, account_id: str) -> None:
        accounts = [
            item for item in self.list_accounts() if item.account_id != account_id
        ]
        self._write_accounts(accounts)
        if self._settings.value(self.SELECTED_KEY, "") == account_id:
            self._settings.remove(self.SELECTED_KEY)
        self._secrets.delete_password(self.SERVICE, account_id)

    def select_account(self, account_id: str) -> None:
        if not any(item.account_id == account_id for item in self.list_accounts()):
            raise ValueError("The selected FTP account was not found.")
        self._settings.setValue(self.SELECTED_KEY, account_id)

    def selected_account(self) -> FtpAccount | None:
        selected_id = self._settings.value(self.SELECTED_KEY, "")
        return next(
            (item for item in self.list_accounts() if item.account_id == selected_id),
            None,
        )

    def password_for(self, account_id: str) -> str | None:
        return self._secrets.get_password(self.SERVICE, account_id)

    def _write_accounts(self, accounts: list[FtpAccount]) -> None:
        self._settings.setValue(
            self.ACCOUNTS_KEY,
            json.dumps([asdict(item) for item in accounts], ensure_ascii=False),
        )


class FtpPublisher:
    """Feltölti a webexport teljes, helyi fájlfáját FTP-n, törlés nélkül."""

    def __init__(self, *, port: int = 21, timeout: float = 20.0):
        if not 1 <= int(port) <= 65535:
            raise ValueError("Érvénytelen FTP-port.")
        self._port = int(port)
        self._timeout = float(timeout)

    def upload(
        self, export_dir: str | Path, account: FtpAccount, password: str
    ) -> int:
        source = Path(export_dir)
        if not source.is_dir():
            raise ValueError("The local web export folder was not found.")
        files = sorted(source.rglob("*"))
        files = [path for path in files if path.is_file()]
        if any(path.is_symlink() for path in files):
            raise ValueError("The web export cannot contain symbolic links.")
        relative_files = [(path, path.relative_to(source).as_posix()) for path in files]
        for _path, relative in relative_files:
            if any(
                part in ("", ".", "..") or any(c in part for c in "\r\n")
                for part in relative.split("/")
            ):
                raise ValueError("A web export contains an unsafe file name.")

        with _FTP(timeout=self._timeout) as ftp:
            ftp.connect(account.domain, self._port)
            ftp.login(account.user, password)
            ftp.cwd("/")
            self._enter_or_create(ftp, account.root)
            for path, relative in relative_files:
                parts = relative.split("/")
                for directory in parts[:-1]:
                    self._enter_or_create(ftp, directory)
                with path.open("rb") as data:
                    ftp.storbinary(f"STOR {parts[-1]}", data)
                ftp.cwd("/")
                self._enter_or_create(ftp, account.root)
        return len(relative_files)

    @staticmethod
    def _enter_or_create(ftp: ftplib.FTP, path: str) -> None:
        segments = [part for part in path.split("/") if part]
        if any(
            part in (".", "..") or any(c in part for c in "\r\n")
            for part in segments
        ):
            raise ValueError("The FTP root folder path is invalid.")
        for segment in segments:
            try:
                ftp.cwd(segment)
            except ftplib.error_perm:
                ftp.mkd(segment)
                ftp.cwd(segment)

"""Google Photos hitelesítés és feltöltés a képtálcából."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Property, QUrl, Slot
from PySide6.QtGui import QDesktopServices

from ..google_photos_fiok import account_email_from_tokens
from .tray_state_controller import _TraySignalsMixin


googlePhotosChanged = _TraySignalsMixin.googlePhotosChanged
photosUploadChanged = _TraySignalsMixin.photosUploadChanged
#: #6446: a belépett fiók e-mail-címe; a tokennel együtt törlődik.
_FIOK_KULCS = "googlePhotos/accountEmail"


class TrayGooglePhotosMixin(_TraySignalsMixin):
    """A tálcán levő képek Google Photos hitelesítési és feltöltési útja."""

    # -- Google Photos feltöltés (#5976) ---------------------------------

    def _ensure_google_photos_wired(self) -> None:
        """A hitelesítési állapotot csak akkor tölti be, amikor a felület kéri."""
        if getattr(self, "_google_photos_wired", False):
            return
        from picasapy.google_photos import CredentialStore, OAuthClient

        self._google_photos_wired = True
        self._google_photos_credentials = CredentialStore(self._get_settings())
        self._google_photos_oauth = OAuthClient()
        self._google_photos_transport = None
        self._google_photos_auth_flow = None
        self._google_photos_auth_busy = False
        self._google_photos_auth_error = ""
        self._photos_upload_running = False
        self._photos_upload_phase = ""
        self._photos_upload_done = 0
        self._photos_upload_total = 0
        self._photos_upload_current_name = ""
        self._photos_upload_error = ""
        self._photos_upload_finished = False
        self._photos_upload_cancel_event = None
        self._photos_upload_pending_paths = None
        self.googlePhotosProgressReported.connect(self._on_photos_upload_progress)
        self.googlePhotosCurrentFileReported.connect(self._on_photos_upload_current_file)
        self.googlePhotosUploadResultReported.connect(self._on_photos_upload_result)
        self.googlePhotosAuthResultReported.connect(self._on_google_photos_auth_result)

    @Property(str, notify=googlePhotosChanged)
    def googlePhotosClientId(self) -> str:
        self._ensure_google_photos_wired()
        return str(self._get_settings().value("googlePhotos/clientId", "") or "")

    @Property(bool, notify=googlePhotosChanged)
    def googlePhotosClientSecretConfigured(self) -> bool:
        self._ensure_google_photos_wired()
        return bool(self._google_photos_credentials.get_secret("client_secret"))

    @Property(bool, notify=googlePhotosChanged)
    def googlePhotosSignedIn(self) -> bool:
        self._ensure_google_photos_wired()
        return bool(
            self._effective_google_photos_credentials()
            and self._google_photos_credentials.get_secret("refresh_token")
        )

    @Property(bool, notify=googlePhotosChanged)
    def googlePhotosCanSignIn(self) -> bool:
        self._ensure_google_photos_wired()
        return self._effective_google_photos_credentials() is not None

    @Property(str, notify=googlePhotosChanged)
    def googlePhotosAccount(self) -> str:
        """A belépett fiók e-mail-címe; üres, ha nincs fiók vagy a belépés régi."""
        self._ensure_google_photos_wired()
        return str(self._get_settings().value(_FIOK_KULCS, "") or "")

    def _set_google_photos_account(self, account: str) -> None:
        """Eltárolja a fiók címét; üres érték törli."""
        settings = self._get_settings()
        if account:
            settings.setValue(_FIOK_KULCS, account)
        else:
            settings.remove(_FIOK_KULCS)

    def _effective_google_photos_credentials(self) -> tuple[str, str] | None:
        """A mentett saját vagy a beépített klienspárt választja ki."""
        from picasapy.google_oauth_beepitett import get_google_oauth_credentials

        return get_google_oauth_credentials(
            self.googlePhotosClientId,
            self._google_photos_credentials.get_secret("client_secret"),
        )

    @Property(bool, notify=googlePhotosChanged)
    def googlePhotosAuthBusy(self) -> bool:
        self._ensure_google_photos_wired()
        return self._google_photos_auth_busy

    @Property(str, notify=googlePhotosChanged)
    def googlePhotosAuthError(self) -> str:
        self._ensure_google_photos_wired()
        return self._google_photos_auth_error

    @Property(bool, notify=googlePhotosChanged)
    def googlePhotosUploadEnabled(self) -> bool:
        self._ensure_google_photos_wired()
        return (
            self.heldCount > 0
            and not self._photos_upload_running
            and not self._google_photos_auth_busy
        )

    @Property(bool, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadRunning(self) -> bool:
        self._ensure_google_photos_wired()
        return self._photos_upload_running

    @Property(str, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadPhase(self) -> str:
        self._ensure_google_photos_wired()
        return self._photos_upload_phase

    @Property(int, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadDone(self) -> int:
        self._ensure_google_photos_wired()
        return self._photos_upload_done

    @Property(int, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadTotal(self) -> int:
        self._ensure_google_photos_wired()
        return self._photos_upload_total

    @Property(str, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadCurrentName(self) -> str:
        self._ensure_google_photos_wired()
        return self._photos_upload_current_name

    @Property(str, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadError(self) -> str:
        self._ensure_google_photos_wired()
        return self._photos_upload_error

    @Property(bool, notify=_TraySignalsMixin.photosUploadChanged)
    def photosUploadFinished(self) -> bool:
        self._ensure_google_photos_wired()
        return self._photos_upload_finished

    @Slot(str, str, result=bool)
    def configureGooglePhotos(self, client_id: str, client_secret: str) -> bool:
        """Az azonosítót a felhasználói beállításba, a titkot a kulcstárba írja."""
        self._ensure_google_photos_wired()
        client_id = str(client_id or "").strip()
        client_secret = str(client_secret or "")
        if not client_id or len(client_id) > 512 or any(ch.isspace() for ch in client_id):
            self._google_photos_auth_error = "missing_credentials"
            self.googlePhotosChanged.emit()
            return False
        if len(client_secret) > 4096:
            self._google_photos_auth_error = "missing_credentials"
            self.googlePhotosChanged.emit()
            return False
        settings = self._get_settings()
        previous_id = str(settings.value("googlePhotos/clientId", "") or "")
        if previous_id != client_id and not client_secret.strip():
            self._google_photos_auth_error = "missing_credentials"
            self.googlePhotosChanged.emit()
            return False
        if previous_id != client_id:
            self._google_photos_credentials.delete_secret("refresh_token")
            self._set_google_photos_account("")
        settings.setValue("googlePhotos/clientId", client_id)
        if client_secret.strip():
            self._google_photos_credentials.set_secret("client_secret", client_secret)
        settings.sync()
        self._google_photos_auth_error = ""
        self.googlePhotosChanged.emit()
        return self.googlePhotosClientSecretConfigured

    @Slot()
    def signInGooglePhotos(self) -> None:
        """Asztali OAuth-ot indít helyi loopback callbackkel."""
        from picasapy.google_photos import GooglePhotosError, LoopbackOAuthSession

        self._ensure_google_photos_wired()
        if self._google_photos_auth_busy:
            return
        if not self.googlePhotosCanSignIn:
            self._google_photos_auth_error = "missing_credentials"
            self.googlePhotosChanged.emit()
            return
        credentials = self._effective_google_photos_credentials()
        if credentials is None:
            self._google_photos_auth_error = "missing_credentials"
            self.googlePhotosChanged.emit()
            return
        client_id, client_secret = credentials
        try:
            flow = LoopbackOAuthSession(
                self._google_photos_oauth,
                client_id=client_id,
                client_secret=client_secret,
            )
        except (OSError, ValueError):
            self._google_photos_auth_error = "auth_failed"
            self.googlePhotosChanged.emit()
            return
        self._google_photos_auth_flow = flow
        self._google_photos_auth_busy = True
        self._google_photos_auth_error = ""
        self.googlePhotosChanged.emit()
        if not QDesktopServices.openUrl(QUrl(flow.authorization_url)):
            flow.cancel()
            self._google_photos_auth_busy = False
            self._google_photos_auth_flow = None
            self._google_photos_auth_error = "browser_unavailable"
            self.googlePhotosChanged.emit()
            return

        def finish_authorization() -> None:
            try:
                tokens = flow.wait_for_tokens()
                refresh_token = str(tokens.get("refresh_token", "") or "")
                if not refresh_token:
                    raise GooglePhotosError("auth_failed")
                account = account_email_from_tokens(tokens)
                self.googlePhotosAuthResultReported.emit(refresh_token, "", account)
            except GooglePhotosError as error:
                self.googlePhotosAuthResultReported.emit("", error.code, "")
            except Exception:
                self.googlePhotosAuthResultReported.emit("", "auth_failed", "")

        self._start_background(
            finish_authorization,
            name="picasapy-google-photos-oauth",
            cancel=flow.cancel,
        )

    @Slot()
    def signOutGooglePhotos(self) -> None:
        """Helyben törli a frissítő tokent; a Google-revokálás legjobb szándékú."""
        self._ensure_google_photos_wired()
        flow = self._google_photos_auth_flow
        if flow is not None:
            flow.cancel()
        refresh_token = self._google_photos_credentials.get_secret("refresh_token")
        self._google_photos_credentials.delete_secret("refresh_token")
        self._set_google_photos_account("")
        self._google_photos_auth_busy = False
        self._google_photos_auth_error = ""
        self.googlePhotosChanged.emit()
        if refresh_token:
            oauth = self._google_photos_oauth
            self._start_background(
                lambda: oauth.revoke(refresh_token),
                name="picasapy-google-photos-revoke",
            )

    @Slot(result=bool)
    def uploadGooglePhotosTray(self) -> bool:
        """A teljes tálca rögzített pillanatképét küldi feltöltésre."""
        from picasapy.google_photos import GooglePhotosApiClient, GooglePhotosError

        self._ensure_google_photos_wired()
        if self._photos_upload_running or self._google_photos_auth_busy:
            return False
        paths = self._photos_upload_pending_paths
        self._photos_upload_pending_paths = None
        if paths is None:
            paths = tuple(str(path) for path in self.heldPaths)
        else:
            paths = tuple(str(path) for path in paths)
        if not paths:
            self._photos_upload_error = "empty_tray"
            self.photosUploadChanged.emit()
            return False
        refresh_token = self._google_photos_credentials.get_secret("refresh_token")
        credentials = self._effective_google_photos_credentials()
        if credentials is None or not refresh_token:
            self._photos_upload_pending_paths = paths
            self._photos_upload_error = ""
            self._photos_upload_phase = "authenticating"
            self._photos_upload_done = 0
            self._photos_upload_total = len(paths)
            self._photos_upload_current_name = ""
            self._photos_upload_finished = False
            self.signInGooglePhotos()
            if not self._google_photos_auth_busy and not self.googlePhotosSignedIn:
                self._photos_upload_pending_paths = None
                self._photos_upload_error = (
                    self._google_photos_auth_error or "auth_failed"
                )
                self._photos_upload_phase = "error"
            self.photosUploadChanged.emit()
            return self._google_photos_auth_busy or self.googlePhotosSignedIn
        client_id, client_secret = credentials
        oauth = self._google_photos_oauth
        transport = self._google_photos_transport
        # `heldPaths` a teljes tálcát adja a beszúrási sorrendjében; a rács
        # pillanatnyi kijelölése és a tálca-tokenek nem kerülnek átadásra.
        cancel_event = threading.Event()
        self._photos_upload_cancel_event = cancel_event
        self._photos_upload_running = True
        self._photos_upload_phase = "preparing"
        self._photos_upload_done = 0
        self._photos_upload_total = len(paths)
        self._photos_upload_current_name = ""
        self._photos_upload_error = ""
        self._photos_upload_finished = False
        self.photosUploadChanged.emit()
        self.googlePhotosChanged.emit()

        def access_token() -> str:
            if not client_id or not client_secret or not refresh_token:
                raise GooglePhotosError("token_expired")
            tokens = oauth.refresh_access_token(
                client_id, client_secret, refresh_token
            )
            token = str(tokens.get("access_token", "") or "")
            if not token:
                raise GooglePhotosError("token_expired")
            return token

        def upload() -> None:
            try:
                token = access_token()
                api = GooglePhotosApiClient(transport=transport)

                def report_progress(phase: str, done: int, total: int) -> None:
                    if phase in {"preparing", "uploading", "uploaded"} and 0 < done <= len(paths):
                        self.googlePhotosCurrentFileReported.emit(Path(paths[done - 1]).name)
                    self.googlePhotosProgressReported.emit(phase, done, total)

                api.upload_paths(
                    paths,
                    access_token=token,
                    progress=report_progress,
                    cancel_event=cancel_event,
                    refresh_access_token=access_token,
                )
                self.googlePhotosUploadResultReported.emit("", True, len(paths))
            except GooglePhotosError as error:
                self.googlePhotosUploadResultReported.emit(error.code, False, len(paths))
            except Exception:
                self.googlePhotosUploadResultReported.emit("api_error", False, len(paths))

        try:
            self._start_background(
                upload,
                name="picasapy-google-photos-upload",
                cancel=cancel_event.set,
            )
        except RuntimeError:
            self._photos_upload_running = False
            self._photos_upload_error = "api_error"
            self.photosUploadChanged.emit()
            self.googlePhotosChanged.emit()
            return False
        return True

    @Slot(list, result=bool)
    def uploadGooglePhotosFromHeaderRows(self, rows) -> bool:
        """A mappa-fejléc sorait rögzíti, majd ugyanazon a feltöltési úton küldi."""
        self._ensure_google_photos_wired()
        if self._photos_upload_running or self._google_photos_auth_busy:
            return False
        paths = []
        photos = getattr(self, "_photos", None)
        if photos is not None:
            for row in rows or ():
                try:
                    path = photos.filePathAt(int(row))
                except (IndexError, TypeError, ValueError):
                    continue
                if path:
                    paths.append(str(path))
        if not paths:
            self._photos_upload_error = "empty_source"
            self._photos_upload_phase = "error"
            self._photos_upload_finished = False
            self.photosUploadChanged.emit()
            return False
        self._photos_upload_pending_paths = tuple(paths)
        return self.uploadGooglePhotosTray()

    @Slot()
    def cancelGooglePhotosUpload(self) -> None:
        self._ensure_google_photos_wired()
        if self._google_photos_auth_busy:
            flow = self._google_photos_auth_flow
            if flow is not None:
                flow.cancel()
            self._google_photos_auth_busy = False
            self._google_photos_auth_flow = None
            self._photos_upload_pending_paths = None
            self._google_photos_auth_error = "cancelled"
            self._photos_upload_error = "cancelled"
            self._photos_upload_phase = "error"
            self.googlePhotosChanged.emit()
            self.photosUploadChanged.emit()
            return
        cancel_event = self._photos_upload_cancel_event
        if self._photos_upload_running and cancel_event is not None:
            cancel_event.set()

    @Slot(str, int, int)
    def _on_photos_upload_progress(self, phase: str, done: int, total: int) -> None:
        self._ensure_google_photos_wired()
        self._photos_upload_phase = phase
        self._photos_upload_done = done
        self._photos_upload_total = total
        self.photosUploadChanged.emit()

    @Slot(str)
    def _on_photos_upload_current_file(self, name: str) -> None:
        self._ensure_google_photos_wired()
        self._photos_upload_current_name = name
        self.photosUploadChanged.emit()

    @Slot(str, bool, int)
    def _on_photos_upload_result(self, error: str, success: bool, total: int) -> None:
        self._ensure_google_photos_wired()
        self._photos_upload_running = False
        self._photos_upload_error = error
        self._photos_upload_finished = success
        self._photos_upload_phase = "completed" if success else "error"
        self._photos_upload_total = total
        if success:
            self._photos_upload_done = total
        self.photosUploadChanged.emit()
        if error == "token_expired":
            self._google_photos_credentials.delete_secret("refresh_token")
            self._set_google_photos_account("")
        self.googlePhotosChanged.emit()

    @Slot(str, str, str)
    def _on_google_photos_auth_result(self, refresh_token: str, error: str, account: str) -> None:
        self._ensure_google_photos_wired()
        pending_paths = self._photos_upload_pending_paths
        self._photos_upload_pending_paths = None
        if refresh_token:
            self._google_photos_credentials.set_secret("refresh_token", refresh_token)
            self._set_google_photos_account(account)
            self._google_photos_auth_error = ""
        else:
            self._set_google_photos_account("")
            self._google_photos_auth_error = error or "auth_failed"
        self._google_photos_auth_busy = False
        self._google_photos_auth_flow = None
        if refresh_token and pending_paths is not None:
            self._photos_upload_pending_paths = pending_paths
            self.uploadGooglePhotosTray()
        elif pending_paths is not None:
            self._photos_upload_error = error or "auth_failed"
            self._photos_upload_phase = "error"
            self.photosUploadChanged.emit()
        self.googlePhotosChanged.emit()

"""Az FTP-fiók adatai tartósak, a jelszó pedig csak a kulcstárba kerül (#5713)."""

# rontás-kontroll: FtpAccountStore.save_account = NotImplementedError → 2 failed

from picasapy.webexport.ftp_publish import FtpAccountStore


class _Settings:
    def __init__(self):
        self.data = {}

    def value(self, key, default=None):
        return self.data.get(key, default)

    def setValue(self, key, value):
        self.data[key] = value

    def remove(self, key):
        self.data.pop(key, None)


class _Secrets:
    def __init__(self):
        self.data = {}

    def get_password(self, service, account_id):
        return self.data.get((service, account_id))

    def set_password(self, service, account_id, password):
        self.data[(service, account_id)] = password

    def delete_password(self, service, account_id):
        self.data.pop((service, account_id), None)


def test_uj_fiok_szerkesztes_valasztas_torles_jelszo_a_kulcstarban():
    settings = _Settings()
    secrets = _Secrets()
    store = FtpAccountStore(settings, secrets)

    account = store.save_account(
        account_id="",
        name="Nyári képek",
        domain="ftp.example.test",
        user="fotós",
        root="/public/album",
        password="jelszó",
    )
    assert account.name == "Nyári képek"
    assert store.password_for(account.account_id) == "jelszó"
    assert "jelszó" not in repr(settings.data)

    edited = store.save_account(
        account_id=account.account_id,
        name="Utazás",
        domain="ftp2.example.test",
        user="uj-user",
        root="/galeria",
        password="",
    )
    assert edited.account_id == account.account_id
    assert edited.domain == "ftp2.example.test"
    assert store.password_for(account.account_id) == "jelszó"

    store.select_account(account.account_id)
    assert store.selected_account().account_id == account.account_id
    store.delete_account(account.account_id)
    assert store.list_accounts() == ()
    assert store.selected_account() is None
    assert store.password_for(account.account_id) is None


def test_a_qml_hid_fiokot_ment_valaszt_lekerdez_es_torol():
    from picasapy.app.webexport_controller import WebExportController

    store = FtpAccountStore(_Settings(), _Secrets())
    controller = WebExportController(
        photo_source=lambda: [], ftp_account_store=store
    )

    saved = controller.saveFtpAccount(
        "", "Képek", "ftp.example.test", "galeria", "/public", "titok"
    )
    assert saved["ok"] is True
    account_id = saved["id"]
    assert controller.ftpAccount(account_id)["domain"] == "ftp.example.test"
    assert controller.selectFtpAccount(account_id) is True
    assert controller.selectedFtpAccountId() == account_id
    assert controller.ftpAccounts()[0]["id"] == account_id
    assert controller.deleteFtpAccount(account_id) is True
    assert controller.ftpAccounts() == []

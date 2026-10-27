# ruff: noqa: F401 -- megőrizzük az edit_controller régi modul-szimbólumait.
"""EditController: a szerkesztőpanel egyetlen QML-hídja."""

from __future__ import annotations

from .edit_controller_shared import (
    AZONOSSAG,
    BETUMERETEK,
    BackgroundWorkerMixin,
    DEAD_LEGACY_OPS,
    EMPTY_HISTOGRAM,
    EditPreviewProvider,
    EditSession,
    EyeCircle64,
    FilterOp,
    FilterWriteError,
    Image,
    IniConflictError,
    IniSaveError,
    LEGACY_EFFECTS,
    LEGACY_EFFECT_KEYS,
    Matrix,
    PICASA_INI_NAME,
    PaintMaskMixin,
    Path,
    PhotoCropReader,
    Property,
    QCoreApplication,
    QEvent,
    QGuiApplication,
    QLocale,
    QObject,
    QSettings,
    QtNamespace,
    Rect64,
    RetouchPatch,
    Signal,
    Slot,
    TextBlock,
    TextGeometry,
    TextOverlay,
    TextOverlaySpec,
    TextStyle,
    UnidentifiedImageError,
    _APPLICABLE_EFFECTS,
    _BRUSH_SIZE_MAX,
    _BRUSH_SIZE_MIN,
    _BRUSH_SIZE_TO_RELATIVE_DIVISOR,
    _DEFAULT_BRUSH_SIZE,
    _DEFAULT_TEXT_ALIGN,
    _DEFAULT_TEXT_BOLD,
    _DEFAULT_TEXT_FILL_COLOR,
    _DEFAULT_TEXT_FILL_ENABLED,
    _DEFAULT_TEXT_ITALIC,
    _DEFAULT_TEXT_OPACITY,
    _DEFAULT_TEXT_OUTLINE_COLOR,
    _DEFAULT_TEXT_OUTLINE_THICKNESS,
    _DEFAULT_TEXT_SIZE_PT,
    _DEFAULT_TEXT_UNDERLINE,
    _EFFECT_INI_NAMES,
    _EFFECT_NAMES,
    _EFFECT_PARAMS,
    _GPU_REVIZIO,
    _LEGACY_EFFECT_NAMES,
    _MOD_NINCS_KITOLTES,
    _ONE_SHOT_NAMES,
    _PICKER_COLOR_PATTERN,
    _PICKER_MRU_SETTINGS_KEYS,
    _REVIZIO,
    _RedeyeBufferState,
    _TOGGLE_NAMES,
    _WRITE_ERRORS,
    _action_key,
    _argb_to_rgb,
    _clamp01,
    _hex_to_rgb,
    _log,
    _rgb_to_argb,
    _rgb_to_hex,
    alignment_code,
    alignment_name,
    build_finetune2_lut,
    can_offer_filter_control,
    chain_flags,
    dataclass,
    default_family,
    encode_rect64,
    estimate_neutral_color,
    family_labels,
    fill_mode_from,
    format_param_values,
    formatting,
    gyors_elonezet,
    has_params,
    invertal,
    is_folder_writable,
    itertools,
    load_or_empty,
    logging,
    meret_taroltbol,
    normalize_crop_ops,
    np,
    one_click_keys,
    parse_faces,
    parse_neutral_argb,
    parse_text,
    parse_text_active,
    re,
    read_exif_details,
    redo_label,
    replace,
    resolve_effect_params,
    serialize_text,
    serialize_text_active,
    suggest_crops,
    tarolt_meret,
    undo_label,
    update_document,
    with_backuphash,
)

from .edit_controller_session_mixin import EditControllerSessionMixin
from .edit_controller_history_mixin import EditControllerHistoryMixin
from .edit_controller_save_mixin import EditControllerSaveMixin
from .edit_controller_preview_mixin import EditControllerPreviewMixin
from .edit_controller_crop_mixin import EditControllerCropMixin
from .edit_controller_retouch_mixin import EditControllerRetouchMixin
from .edit_controller_redeye_mixin import EditControllerRedeyeMixin
from .edit_controller_text_mixin import EditControllerTextMixin
from .edit_controller_effects_mixin import EditControllerEffectsMixin
from .edit_controller_signals import EditControllerSignalsMixin

class EditController(
    EditControllerSessionMixin,
    EditControllerHistoryMixin,
    EditControllerSaveMixin,
    EditControllerPreviewMixin,
    EditControllerCropMixin,
    EditControllerRetouchMixin,
    EditControllerRedeyeMixin,
    EditControllerTextMixin,
    EditControllerEffectsMixin,
    EditControllerSignalsMixin,
    PaintMaskMixin,
    QObject,
    BackgroundWorkerMixin,
):
    """A QML-híd neve és konstruktor-szerződése változatlan.

    A témák sima Python-mixinekben élnek. A jelzések is sima mixinből
    öröklődnek: a korábbi QObject-leszármazott alias-megosztás SIGSEGV-t
    okozott (#148).
    """

    SAJAT_LASSU_SZUROK = frozenset({"crossprocess"})

    def __init__(
        self,
        provider: EditPreviewProvider,
        parent=None,
        *,
        slot: str = "",
        settings: QSettings | None = None,
    ) -> None:
        """`slot` (#3187): melyik ELŐNÉZET-REKESZ a vezérlőé.

        A kettős nézet második fele önálló szerkesztési állapotot kaphat —
        az eredetiben teljes értékű második előnézet áll
        (`editpanel/preview2`, `editpanel/previewclip2`). A szolgáltató
        gyorsítótára a fotó azonosítójával kulcsozódik, tehát UGYANARRA a
        fotóra nyitott két munkamenet felülírná egymás képét. A rekesz a
        kulcsot jelöli meg (`<fotó>@<rekesz>`); a LOGIKAI fotó-azonosító
        (ini-írás, mentés) változatlan marad.

        Üres rekesz = a mai, egyetlen munkamenet; a kulcs ilyenkor
        betűre ugyanaz, mint eddig."""
        super().__init__(parent)
        self._provider = provider
        self._slot = str(slot or "")
        self._picker_settings = (
            settings if settings is not None else QSettings("PicasaPy", "PicasaPy")
        )
        # #514: az előnézet-renderelések sorszáma. Minden új kérés növeli;
        # a háttérszálra tett (lassú) renderelés a saját sorszámát
        # összeveti az aktuálissal, és ELAVULTKÉNT kihagyja magát, ha
        # időközben újabb kérés érkezett — így egy gyors kattintás-sorozat
        # csak az UTOLSÓ állapotot rendereli ki, és sosem írhat vissza egy
        # régebbi képet a frissebb fölé.
        self._preview_job = 0
        self._previewRendered.connect(self._on_preview_rendered)
        # #798: a Shift élő követése. Az eseményszűrő az ALKALMAZÁSRA megy,
        # mert a billentyű-esemény a fókuszált elemhez érkezik, nem a
        # vezérlőhöz — az effekt-rácsnak viszont fókusz nélkül is tudnia
        # kell róla.
        self._shift_aktiv = False
        self._shift_figyeles = False
        self._photo_id = ""
        self._image_path: Path | None = None
        # #3014: az „aa" mód NEM kijelölt fele csak memóriában szerkeszt —
        # a két fél ugyanazt a `filters=` sort írná felül egymás elől. A
        # kilépéskori döntés (`persistChain`) írja ki, ha ezt kell megtartani.
        self._memory_only = False
        # #3649: az „aa" mód PÁRJA (`link_aa_partner`, application.py) — a
        # fókuszváltás (`swapAaFocus`) ezen át cseréli a festett maszkot a
        # két fél között, hogy a félkész festés ne ürüljön ki.
        self._aa_partner: EditController | None = None
        # #516: a képfüggő effekt-tartományok (pl. `CornerRadius` 0..
        # min(W,H)/2) kiszámolásához — csak a fejlécet olvassuk (PIL nem
        # dekódolja a pixeleket), `beginEdit`-enként újraszámolva
        self._image_size: tuple[int, int] | None = None
        self._ini_path: Path | None = None
        self._section_name = ""
        self._crop_reader = PhotoCropReader()
        self._opening_crop: str | None = None
        self._opening_crop_ini_readable = True
        self._opening_crop_ops: tuple[FilterOp, ...] = ()
        self._session = EditSession()
        self._revision = 0
        # GPU élő-előnézet (#22): önálló számláló, ld. gpuRevisionChanged
        self._gpu_revision = 0
        # undo/redo verem (#59): (filters-érték a művelet ELŐTT, művelet-kulcs)
        self._undo_stack: list[tuple[str, str]] = []
        self._redo_stack: list[tuple[str, str]] = []
        # fényképezőgép-összefoglaló (#25): a forrásfájl EXIF-jéből, csak a
        # beginEdit-kor olvasva — a szerkesztés alatt nem változik, a
        # csúszka-húzás minden egyes revíziójánál újraolvasni felesleges lenne
        self._camera_summary = ""
        # retusálás (#445): a Vágás-mintájú enter/exit + Alkalmaz/Mégse
        # eszközhöz a kétkattintásos, irányított klónozással (cél→forrás)
        # hozott, MÉG NEM mentett foltok puffere — Alkalmazásig csak az élő
        # előnézetet befolyásolja, ini-t nem ír. A `_retouch_target` az
        # ELSŐ kattintással kijelölt, de a forrás-pont hiányában még nem
        # véglegesített folt cél-pontja (None, ha nincs ilyen félbehagyott
        # folt). A patch-enkénti Undo/Redo/Reset EZEN a pufferen dolgozik —
        # a globális (`_undo_stack`) verem csak az Alkalmazott retusálást
        # látja EGY lépésként, a foltok belső részleteit nem.
        self._init_paint_mask()
        self._retouch_patches: tuple[RetouchPatch, ...] = ()
        self._retouch_target: tuple[float, float] | None = None
        self._retouch_patch_undo: list[tuple[RetouchPatch, ...]] = []
        self._retouch_patch_redo: list[tuple[RetouchPatch, ...]] = []
        # vörösszem (#445/#4261/#4541): a Retusáláséval azonos szerkezetű,
        # MÉG NEM mentett puffer. Az automatikus körökből a panel négyzeteket
        # rajzol, kattintásra pedig ugyanebből a körlistából törlünk, amely a
        # renderelőhöz jut. A régiópuffer a kézi kiegészítéseket tárolja.
        self._redeye_regions: tuple[Rect64, ...] = ()
        self._redeye_region_undo: list[_RedeyeBufferState] = []
        self._redeye_eye_circles: tuple[tuple[float, float, float], ...] = ()
        self._redeye_eye_image_size: tuple[int, int] | None = None
        self._redeye_eye_overlay_size: tuple[int, int] | None = None
        self._redeye_eye_to_overlay: Matrix = AZONOSSAG
        self._redeye_full_image_fallback = False
        # az automatika utolsó futásának találat-száma (-1: még nem futott)
        self._redeye_found = -1
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False
        # #448: a vágás-javaslatokhoz kért képarány (None = a forráskép
        # arányát tartjuk); a vágó-panel arány-választója állítja
        self._crop_aspect: float | None = None
        # kör alakú ecset mérete (#445) — munkamenet-szintű állapot (a
        # szöveg-stílushoz hasonlóan NEM kerül a `.picasa.ini`-be), minden
        # szerkesztés-nyitáskor alapértékre áll.
        self._brush_size: int = _DEFAULT_BRUSH_SIZE
        # szöveg-overlay (#148): a mentett `text=`/`textactive=` értékek
        # típusos alakja (None, ha nincs — vagy a bejegyzés nem értelmezhető,
        # a #301-elv szerint), plusz a szerkesztés alatti, MÉG NEM mentett
        # piszkozat (tartalom + kattintott pozíció).
        self._text_overlay: TextOverlay | None = None
        self._text_selected_index: int | None = None
        self._text_active = False
        # A showtextcheckbox csak az előnézet rajzát kapcsolja; nem írja át
        # a mentett szöveget vagy a textactive mezőt.
        self._text_overlay_visible = True
        self._text_draft = ""
        self._text_pending_pos: tuple[float, float] | None = None
        # szöveg-megjelenítési stílus (#450): a színek, méret és igazítás
        # munkamenet-szintű állapot; a betűcsalád kivétel, azt a `text=`
        # mezőből visszaolvassuk, és mentéskor oda írjuk.
        self._text_fill_color: tuple[int, int, int] = _DEFAULT_TEXT_FILL_COLOR
        self._text_outline_color: tuple[int, int, int] = _DEFAULT_TEXT_OUTLINE_COLOR
        self._text_outline_thickness: int = _DEFAULT_TEXT_OUTLINE_THICKNESS
        self._text_fill_enabled: bool = _DEFAULT_TEXT_FILL_ENABLED
        self._text_opacity: float = _DEFAULT_TEXT_OPACITY
        self._text_family: str = default_family()
        self._text_size_pt: int = _DEFAULT_TEXT_SIZE_PT
        self._text_size_edited = False
        self._text_bold: bool = _DEFAULT_TEXT_BOLD
        self._text_italic: bool = _DEFAULT_TEXT_ITALIC
        self._text_underline: bool = _DEFAULT_TEXT_UNDERLINE
        self._text_align: str = _DEFAULT_TEXT_ALIGN


    def eventFilter(self, figyelt, esemeny) -> bool:  # noqa: N802 — Qt-név
        """A Shift le- és felengedésének követése (#798).

        A szűrő SOHA nem nyeli el az eseményt: csak megjegyzi az állapotot
        és jelez, ha változott. Az ismétlődő (nyomva tartott) lenyomás nem
        ad új jelzést — különben a kötések feleslegesen pörögnének.
        """
        tipus = esemeny.type()
        if tipus in (QEvent.Type.KeyPress, QEvent.Type.KeyRelease):
            kulcs = getattr(esemeny, "key", None)
            if kulcs is not None and kulcs() == QtNamespace.Key.Key_Shift:
                self._allitsd_a_shiftet(tipus == QEvent.Type.KeyPress)
        return super().eventFilter(figyelt, esemeny)


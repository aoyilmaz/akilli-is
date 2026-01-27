"""
Proje genelinde kullanılan ikon tanımları (Phosphor Icons).
Tek bir noktadan yönetilebilir ikon seti.
"""


class ICONS:
    # --- NAVİGASYON & AKSİYON ---
    BACK = "ph.arrow-left"
    FORWARD = "ph.arrow-right"
    REFRESH = "ph.arrows-clockwise"
    HOME = "ph.house"
    MENU = "ph.list"
    CLOSE = "ph.x"
    TRUCK = "ph.truck"
    BUILDING = "ph.buildings"
    FOLDER_OPEN = "ph.folder-open"
    CHECK = "ph.check"
    PLUS = "ph.plus"
    MINUS = "ph.minus"
    EDIT = "ph.pencil-simple"
    DELETE = "ph.trash"
    SAVE = "ph.floppy-disk"
    CANCEL = "ph.prohibit"
    SEARCH = "ph.magnifying-glass"
    FILTER = "ph.funnel"
    EXPORT = "ph.export"
    IMPORT = "ph.download"
    PRINT = "ph.printer"
    COPY = "ph.copy"
    EYE = "ph.eye"
    SETTINGS = "ph.gear"
    LOGOUT = "ph.sign-out"
    USER = "ph.user"
    USERS = "ph.users"

    # --- STOK & ENVANTER ---
    INVENTORY = "ph.package"
    STOCK_CARD = "ph.cardholder"
    WAREHOUSE = "ph.house-line"
    MOVEMENT = "ph.arrows-left-right"
    CATEGORY = "ph.tag"
    TAG = "ph.tag"
    BARCODE = "ph.barcode"
    QR = "ph.qr-code"

    # Stok Tipleri
    TYPE_RAW = "ph.cube"  # Hammadde
    TYPE_PRODUCT = "ph.package"  # Mamül
    TYPE_SEMI = "ph.gear"  # Yarı Mamül
    TYPE_PACKAGE = "ph.gift"  # Ambalaj
    TYPE_CONSUMABLE = "ph.wrench"  # Sarf
    TYPE_COMMERCIAL = "ph.tag"  # Ticari
    TYPE_SERVICE = "ph.briefcase"  # Hizmet
    TYPE_OTHER = "ph.clipboard-text"  # Diğer

    # --- FİNANS & MUHASEBE ---
    FINANCE = "ph.currency-try"  # TL simgesi yoksa yerine
    MONEY = "ph.money"
    BANK = "ph.bank"
    INVOICE = "ph.receipt"
    PAYMENT = "ph.credit-card"
    WALLET = "ph.wallet"
    TREND_UP = "ph.trend-up"
    TREND_DOWN = "ph.trend-down"

    # --- ÜRETİM ---
    PRODUCTION = "ph.factory"
    WORK_ORDER = "ph.clipboard"
    MACHINE = "ph.robot"  # veya ph.engine
    PLANNING = "ph.calendar-check"
    CALENDAR = "ph.calendar"
    OPERATION = "ph.activity"
    PLAY = "ph.play"
    PAUSE = "ph.pause"
    STOP = "ph.stop"
    FLASK = "ph.flask"
    PACKAGE_MINUS = "ph.package-minus"
    MINUS_CIRCLE = "ph.minus-circle"
    HISTORY = "ph.clock-counter-clockwise"

    # --- BAKIM ---
    MAINTENANCE = "ph.wrench"
    FIX = "ph.hammer"
    DOWNTIME = "ph.stop-circle"
    TIME = "ph.clock"

    # --- İK & CRM ---
    HR = "ph.users-three"
    EMPLOYEE = "ph.identification-badge"
    CRM = "ph.handshake"
    DEAL = "ph.star"
    CUSTOMER = "ph.user-focus"
    ROCKET = "ph.rocket"
    TARGET = "ph.target"
    LOCATION = "ph.map-pin"
    PHONE = "ph.phone"
    SPARKLE = "ph.sparkle"

    # --- ALERT & DURUM ---
    WARNING = "ph.warning"
    ERROR = "ph.warning-circle"  # Critical
    INFO = "ph.info"
    SUCCESS = "ph.check-circle"
    DANGER = "ph.x-circle"
    LOCKED = "ph.lock"
    UNLOCKED = "ph.lock-open"

    # --- DURUM İKONLARI (Tablolar için) ---
    STATUS_ICONS = {
        "active": "ph.check-circle",
        "passive": "ph.prohibit",
        "success": "ph.check-circle",
        "warning": "ph.warning",
        "error": "ph.warning-circle",
        "danger": "ph.x-circle",
        "info": "ph.info",
        "pending": "ph.clock",
        # Stock status
        "out_of_stock": "ph.x-circle",
        "critical": "ph.warning-circle",
        "low": "ph.warning",
        "normal": "ph.check-circle",
    }

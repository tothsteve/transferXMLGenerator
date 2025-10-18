export const MESSAGES = {
  // Common messages
  LOADING: 'Betöltés...',
  SAVING: 'Mentés...',
  DELETING: 'Törlés...',
  PROCESSING: 'Feldolgozás...',

  // Success messages
  SUCCESS: {
    BENEFICIARY_CREATED: 'Kedvezményezett sikeresen létrehozva',
    BENEFICIARY_UPDATED: 'Kedvezményezett sikeresen frissítve',
    BENEFICIARY_DELETED: 'Kedvezményezett sikeresen törölve',

    TEMPLATE_CREATED: 'Sablon sikeresen létrehozva',
    TEMPLATE_UPDATED: 'Sablon sikeresen frissítve',
    TEMPLATE_DELETED: 'Sablon sikeresen törölve',
    TEMPLATE_LOADED: 'Sablon sikeresen betöltve',

    TRANSFERS_CREATED: 'Átutalások sikeresen létrehozva',
    XML_GENERATED: 'XML fájl sikeresen generálva',
    XML_DOWNLOADED: 'XML fájl sikeresen letöltve',
    XML_COPIED: 'XML tartalom vágólapra másolva',

    EXCEL_IMPORTED: 'Excel fájl sikeresen importálva',
    FILE_UPLOADED: 'Fájl sikeresen feltöltve',
  },

  // Error messages
  ERROR: {
    GENERIC: 'Váratlan hiba történt',
    NETWORK: 'Hálózati hiba - ellenőrizze az internetkapcsolatot',
    SERVER: 'Szerver hiba - próbálja újra később',
    UNAUTHORIZED: 'Nincs jogosultsága a művelet végrehajtásához',
    FORBIDDEN: 'Nincs engedélye a művelet végrehajtásához',
    NOT_FOUND: 'A keresett erőforrás nem található',
    VALIDATION: 'Érvénytelen adatok - ellenőrizze a bevitt információkat',

    BENEFICIARY_CREATE: 'Hiba a kedvezményezett létrehozásakor',
    BENEFICIARY_UPDATE: 'Hiba a kedvezményezett frissítésekor',
    BENEFICIARY_DELETE: 'Hiba a kedvezményezett törlésekor',

    TEMPLATE_CREATE: 'Hiba a sablon létrehozásakor',
    TEMPLATE_UPDATE: 'Hiba a sablon frissítésekor',
    TEMPLATE_DELETE: 'Hiba a sablon törlésekor',
    TEMPLATE_LOAD: 'Hiba a sablon betöltésekor',

    TRANSFERS_CREATE: 'Hiba az átutalások létrehozásakor',
    XML_GENERATE: 'Hiba az XML generálásakor',
    XML_DOWNLOAD: 'Hiba az XML letöltésekor',
    XML_COPY: 'Hiba a vágólapra másoláskor',

    EXCEL_IMPORT: 'Hiba az Excel fájl importálásakor',
    FILE_UPLOAD: 'Hiba a fájl feltöltésekor',
    FILE_SIZE: 'A fájl mérete túl nagy',
    FILE_TYPE: 'Nem támogatott fájltípus',
  },

  // Confirmation messages
  CONFIRM: {
    DELETE_BENEFICIARY: 'Biztosan törölni szeretné ezt a kedvezményezettet?',
    DELETE_TEMPLATE: 'Biztosan törölni szeretné ezt a sablont?',
    DELETE_TRANSFER: 'Biztosan törölni szeretné ezt az átutalást?',
    CLEAR_TRANSFERS: 'Biztosan törölni szeretné az összes átutalást?',
    OVERWRITE_TEMPLATE: 'A sablon betöltése felülírja a jelenlegi átutalásokat. Folytatja?',
  },

  // Validation messages
  VALIDATION: {
    REQUIRED: 'Ez a mező kötelező',
    INVALID_EMAIL: 'Érvénytelen email cím',
    INVALID_ACCOUNT: 'Érvénytelen számlaszám formátum',
    INVALID_AMOUNT: 'Érvénytelen összeg',
    INVALID_DATE: 'Érvénytelen dátum',
    MIN_AMOUNT: 'Az összegnek pozitívnak kell lennie',
    MAX_LENGTH: 'Túl hosszú szöveg',

    BENEFICIARY_NAME_REQUIRED: 'A kedvezményezett neve kötelező',
    ACCOUNT_NUMBER_REQUIRED: 'A számlaszám megadása kötelező',
    AMOUNT_REQUIRED: 'Az összeg megadása kötelező',
    EXECUTION_DATE_REQUIRED: 'A teljesítés dátuma kötelező',
    TEMPLATE_NAME_REQUIRED: 'A sablon neve kötelező',
  },

  // Info messages
  INFO: {
    NO_BENEFICIARIES: 'Nincsenek kedvezményezettek',
    NO_TEMPLATES: 'Nincsenek sablonok',
    NO_TRANSFERS: 'Nincsenek átutalások',
    NO_SEARCH_RESULTS: 'Nincs találat a keresésre',

    EXCEL_FORMAT: 'Támogatott formátumok: XLSX, XLS, CSV (max. 10MB)',
    TEMPLATE_HELP: 'A sablonok segítségével ismétlődő átutalásokat gyorsan létrehozhat',
    XML_FORMAT: 'A generált XML kompatibilis a magyar bankok rendszereivel',
  },

  // Status messages
  STATUS: {
    ACTIVE: 'Aktív',
    INACTIVE: 'Inaktív',
    FREQUENT: 'Gyakori',
    PROCESSED: 'Feldolgozva',
    PENDING: 'Függőben',
    DRAFT: 'Piszkozat',
  },

  // Labels
  LABELS: {
    NAME: 'Név',
    ACCOUNT_NUMBER: 'Számlaszám',
    BANK_NAME: 'Bank neve',
    AMOUNT: 'Összeg',
    CURRENCY: 'Deviza',
    EXECUTION_DATE: 'Teljesítés dátuma',
    REMITTANCE_INFO: 'Közlemény',
    DESCRIPTION: 'Leírás',
    TEMPLATE_NAME: 'Sablon neve',
    BENEFICIARY_COUNT: 'Kedvezményezettek száma',
    TOTAL_AMOUNT: 'Összeg összesen',
    CREATED_AT: 'Létrehozva',
    UPDATED_AT: 'Módosítva',
  },
};

export const CURRENCIES = {
  HUF: 'Magyar forint',
  EUR: 'Euró',
  USD: 'Amerikai dollár',
};

export const DATE_FORMATS = {
  SHORT: 'YYYY.MM.DD',
  LONG: 'YYYY. MMMM DD.',
  DISPLAY: 'hu-HU',
};

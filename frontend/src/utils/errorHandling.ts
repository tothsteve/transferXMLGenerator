import { AxiosError } from 'axios';

export interface ApiError {
  message: string;
  field?: string;
  code?: string;
}

export const getErrorMessage = (error: unknown): string => {
  if (!error) return 'Ismeretlen hiba történt';

  if (error instanceof AxiosError) {
    // Server provided error message
    if (error.response?.data?.message) {
      return error.response.data.message;
    }

    // Server provided error details
    if (error.response?.data?.detail) {
      return error.response.data.detail;
    }

    // Server provided field errors
    if (error.response?.data?.errors && Array.isArray(error.response.data.errors)) {
      return error.response.data.errors[0]?.message || 'Validációs hiba';
    }

    // HTTP status based messages
    switch (error.response?.status) {
      case 400:
        return 'Hibás kérés - ellenőrizze a megadott adatokat';
      case 401:
        return 'Nincs jogosultsága a művelet végrehajtásához';
      case 403:
        return 'Nincs engedélye a művelet végrehajtásához';
      case 404:
        return 'A keresett erőforrás nem található';
      case 409:
        return 'Konfliktus - az erőforrás már létezik vagy használatban van';
      case 422:
        return 'Érvénytelen adatok - ellenőrizze a bevitt információkat';
      case 500:
        return 'Szerver hiba - próbálja újra később';
      case 503:
        return 'A szolgáltatás jelenleg nem elérhető';
      default:
        return `Hiba történt (${error.response?.status})`;
    }
  }

  if (error instanceof Error) {
    return error.message;
  }

  if (typeof error === 'string') {
    return error;
  }

  return 'Váratlan hiba történt';
};

export const getSuccessMessage = (action: string, entity: string): string => {
  const messages = {
    create: {
      beneficiary: 'Kedvezményezett sikeresen létrehozva',
      template: 'Sablon sikeresen létrehozva',
      transfer: 'Átutalás sikeresen létrehozva',
      batch: 'Köteg sikeresen létrehozva',
    },
    update: {
      beneficiary: 'Kedvezményezett sikeresen frissítve',
      template: 'Sablon sikeresen frissítve',
      transfer: 'Átutalás sikeresen frissítve',
      batch: 'Köteg sikeresen frissítve',
    },
    delete: {
      beneficiary: 'Kedvezményezett sikeresen törölve',
      template: 'Sablon sikeresen törölve',
      transfer: 'Átutalás sikeresen törölve',
      batch: 'Köteg sikeresen törölve',
    },
    import: {
      beneficiary: 'Kedvezményezettek sikeresen importálva',
      excel: 'Excel fájl sikeresen feldolgozva',
    },
    generate: {
      xml: 'XML fájl sikeresen generálva',
    },
    load: {
      template: 'Sablon sikeresen betöltve',
    },
  };

  return (messages as any)[action]?.[entity] || `${entity} sikeresen ${action === 'create' ? 'létrehozva' : 'módosítva'}`;
};
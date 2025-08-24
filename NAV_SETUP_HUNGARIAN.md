# NAV Online Számla Integráció Beállítási Útmutató

Ez az útmutató lépésről lépésre bemutatja a NAV Online Számla rendszerrel való integráció beállítását.

## Áttekintés

A Transfer XML Generator alkalmazás automatikusan szinkronizálja a NAV Online Számla rendszerből a számla adatokat, amely lehetővé teszi:

- **Automatikus számla szinkronizálás** - A NAV rendszerből automatikusan letölti a számla adatokat
- **Kedvezményezettek automatikus létrehozása** - A számlák alapján automatikusan létrehozza a hiányzó kedvezményezetteket
- **Konszolidált utalások** - Összevonja az azonos kedvezményezettnek szóló összegeket
- **Átfogó jelentések** - Részletes jelentéseket készít a szinkronizált adatokról

## 1. NAV Felhasználói Fiók Beállítása

### 1.1 Technikai Felhasználó Létrehozása

1. **Belépés a NAV Online Számla felületre**
   - Látogasson el a [https://onlineszamla.nav.gov.hu](https://onlineszamla.nav.gov.hu) oldalra
   - Jelentkezzen be a cég adószámával és jelszavával

2. **Technikai felhasználó menü**
   - Navigáljon a **"Technikai felhasználók"** menüpontra
   - Kattintson az **"Új technikai felhasználó"** gombra

3. **Technikai felhasználó adatok**
   - **Felhasználónév**: Válasszon egyedi felhasználónevet (pl: `cegnev-api-user`)
   - **Jelszó**: Állítson be erős jelszót (min. 8 karakter, nagy- és kisbetűk, számok, speciális karakterek)
   - **E-mail cím**: Adja meg a technikai kapcsolattartó e-mail címét
   - **Jogosultságok**: Válassza ki a szükséges jogosultságokat:
     - ✅ **Számla lekérdezés**
     - ✅ **Számla adat lekérdezés**
     - ✅ **Tranzakció státusz lekérdezés**

4. **Mentés és aktiválás**
   - Kattintson a **"Mentés"** gombra
   - A technikai felhasználó automatikusan aktiválásra kerül

### 1.2 Tanúsítványok Generálása

1. **Aláíró tanúsítvány létrehozása**
   - A technikai felhasználó részleteit megnyitva kattintson **"Aláíró tanúsítvány generálása"**
   - Töltse le a generált `.p12` fájlt
   - Jegyezze fel a tanúsítvány jelszavát

2. **Csere tanúsítvány létrehozása**
   - Kattintson **"Csere tanúsítvány generálása"**
   - Töltse le a generált `.p12` fájlt
   - Jegyezze fel a tanúsítvány jelszavát

3. **Tanúsítványok konvertálása**
   
   Az alkalmazás PEM formátumú tanúsítványokat vár. Konvertálja a `.p12` fájlokat:

   **Aláíró tanúsítvány konvertálása:**
   ```bash
   # Privát kulcs kinyerése
   openssl pkcs12 -in signing-cert.p12 -nocerts -nodes -out signing-key.pem
   
   # Tanúsítvány kinyerése
   openssl pkcs12 -in signing-cert.p12 -clcerts -nokeys -out signing-cert.pem
   ```

   **Csere tanúsítvány konvertálása:**
   ```bash
   # Privát kulcs kinyerése
   openssl pkcs12 -in exchange-cert.p12 -nocerts -nodes -out exchange-key.pem
   
   # Tanúsítvány kinyerése
   openssl pkcs12 -in exchange-cert.p12 -clcerts -nokeys -out exchange-cert.pem
   ```

## 2. Alkalmazás NAV Konfiguráció

### 2.1 Admin Felület Elérése

1. **Bejelentkezés**
   - Látogasson el az alkalmazás admin felületére: `https://yourdomain.com/admin/`
   - Jelentkezzen be az adminisztrátori fiókjával

2. **NAV Konfigurációk menü**
   - Kattintson **"Bank Transfers"** → **"NAV Configurations"**

### 2.2 NAV Konfiguráció Létrehozása

Minden cég számára külön NAV konfigurációt kell létrehozni:

1. **Kattintson "Add NAV Configuration"**

2. **Alapadatok megadása:**
   - **Company**: Válassza ki a céget a listából
   - **Tax number**: A cég 8 számjegyű adószáma (pl: `12345678`)
   - **API Environment**: 
     - **`test`**: Teszt környezet használata fejlesztéshez
     - **`production`**: Éles környezet használata

3. **Hitelesítési adatok (automatikusan titkosításra kerülnek):**
   - **Technical user login**: A NAV technikai felhasználó neve
   - **Technical user password**: A NAV technikai felhasználó jelszava
   - **Signing key**: A konvertált aláíró tanúsítvány teljes tartalma (signing-key.pem + signing-cert.pem)
   - **Exchange key**: A konvertált csere tanúsítvány teljes tartalma (exchange-key.pem + exchange-cert.pem)

   **Tanúsítvány fájlok egyesítése:**
   ```bash
   # Aláíró tanúsítvány egyesítése
   cat signing-key.pem signing-cert.pem > signing-combined.pem
   
   # Csere tanúsítvány egyesítése
   cat exchange-key.pem exchange-cert.pem > exchange-combined.pem
   ```

   A `signing-combined.pem` tartalmát másolja a **Signing key** mezőbe, 
   az `exchange-combined.pem` tartalmát pedig az **Exchange key** mezőbe.

4. **Szinkronizálási beállítások:**
   - **Sync enabled**: Pipálja be az automatikus szinkronizálás engedélyezéséhez
   - **Sync frequency hours**: Szinkronizálás gyakorisága órákban (ajánlott: 12)

5. **Mentés**
   - Kattintson **"Save"** a konfiguráció mentéséhez

## 3. Konfiguráció Tesztelése

### 3.1 Kapcsolat Tesztelése

Terminálban futtassa a következő parancsot:

```bash
cd /path/to/transferXMLGenerator/backend
source ../venv/bin/activate

# Kapcsolat tesztelése (cserélje ki az 1-et a cég ID-jával)
python manage.py test_nav_connection --company-id=1
```

**Sikeres kapcsolat esetén:**
```
NAV connection test successful for company: Cég Neve
- Tax number: 12345678
- Environment: production
- API endpoint reachable: ✓
- Authentication successful: ✓
```

**Hiba esetén:**
```
NAV connection test failed:
- Error: Invalid credentials
- Please check technical user login and password
```

### 3.2 Teszt Szinkronizálás

Próbálja ki a szinkronizálást teszt módban:

```bash
# Teszt szinkronizálás (nem ír adatbázisba)
python manage.py sync_nav_invoices --company-id=1 --dry-run

# Éles szinkronizálás
python manage.py sync_nav_invoices --company-id=1
```

**Sikeres szinkronizálás kimenet:**
```
Starting NAV invoice sync for company: Cég Neve
- Syncing invoices from 2024-01-01 to 2024-12-31
- Found 150 invoices to process
- Created 45 new beneficiaries
- Processed 150 invoices successfully
- Sync completed in 2.5 minutes
```

## 4. Automatikus Szinkronizálás Beállítása

### 4.1 Cron Job Hozzáadása

Automatikus szinkronizáláshoz adja hozzá a következő bejegyzést a crontab-hoz:

```bash
# Crontab szerkesztése
crontab -e

# 12 óránként szinkronizálás (cserélje ki az 1-et a cég ID-jával)
0 */12 * * * cd /path/to/transferXMLGenerator/backend && /path/to/venv/bin/python manage.py sync_nav_invoices --company-id=1 >> /var/log/transferxml/nav_sync.log 2>&1
```

### 4.2 Naplózás Beállítása

Hozza létre a naplókönyvtárat és állítsa be a jogosultságokat:

```bash
sudo mkdir -p /var/log/transferxml
sudo chown app:app /var/log/transferxml
sudo chmod 755 /var/log/transferxml
```

## 5. Működés Ellenőrzése

### 5.1 Szinkronizált Adatok Ellenőrzése

1. **Admin felületen:**
   - **Companies** → Válassza ki a céget → **Invoices** 
   - Ellenőrizze, hogy megjelentek-e a NAV számlák

2. **Kedvezményezettek ellenőrzése:**
   - **Beneficiaries** menü
   - Ellenőrizze, hogy létrejöttek-e új kedvezményezettek a számlák alapján

### 5.2 Napló Ellenőrzése

```bash
# Szinkronizálási napló megtekintése
tail -f /var/log/transferxml/nav_sync.log

# Alkalmazás napló
tail -f /var/log/transferxml/app.log
```

## 6. Hibaelhárítás

### Gyakori Hibák és Megoldások

#### 6.1 "Invalid credentials" hiba

**Probléma:** Helytelen technikai felhasználó adatok
**Megoldás:**
1. Ellenőrizze a technikai felhasználó nevét és jelszavát a NAV felületen
2. Győződjön meg róla, hogy a felhasználó aktív
3. Frissítse az alkalmazásban a hitelesítési adatokat

#### 6.2 "Certificate error" hiba

**Probléma:** Hibás tanúsítvány formátum vagy tartalom
**Megoldás:**
1. Ellenőrizze a tanúsítvány konvertálást
2. Győződjön meg róla, hogy a privát kulcs és a tanúsítvány is szerepel
3. Ellenőrizze, hogy nincs-e extra szóköz vagy speciális karakter

#### 6.3 "Tax number not found" hiba

**Probléma:** Helytelen adószám
**Megoldás:**
1. Ellenőrizze, hogy a helyes 8 számjegyű adószám van megadva
2. Győződjön meg róla, hogy a cég regisztrálva van a NAV Online Számla rendszerben

#### 6.4 "API quota exceeded" hiba

**Probléma:** Túllépte a NAV API napi kvótát
**Megoldás:**
1. Csökkentse a szinkronizálás gyakoriságát
2. Használjon kisebb dátum tartományokat
3. Várjon a kvóta újratöltésére (általában éjfélkor)

### 6.5 Részletes Hibanaplózás

Részletesebb naplózáshoz állítsa be a DEBUG szintet:

```python
# settings.py-ban
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/var/log/transferxml/nav_debug.log',
        },
    },
    'loggers': {
        'bank_transfers.nav_client': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```

## 7. Biztonsági Megjegyzések

### 7.1 Tanúsítványok Biztonsága

- **Soha ne ossza meg** a tanúsítvány fájlokat
- **Tárolja biztonságos helyen** a .p12 fájlokat és jelszavakat
- **Rendszeresen ellenőrizze** a tanúsítványok lejárati dátumát
- **Korlátozott hozzáférés** - csak a szükséges személyek férjenek hozzá

### 7.2 Felhasználói Fiókok

- **Erős jelszavak** használata minden technikai felhasználóhoz
- **Rendszeres jelszóváltoztatás** (3-6 havonta)
- **Többfaktoros hitelesítés** engedélyezése ahol lehetséges

### 7.3 Hálózati Biztonság

- **HTTPS használata** minden NAV API híváshoz
- **Tűzfal beállítás** - csak szükséges portok nyitottak
- **VPN használata** érzékeny műveletekhez

## 8. Támogatás és Karbantartás

### 8.1 Rendszeres Feladatok

**Hetente:**
- NAV szinkronizálás státusz ellenőrzése
- Hibanaplók áttekintése
- Teljesítmény figyelése

**Havonta:**
- Tanúsítványok lejárati dátumának ellenőrzése
- Szinkronizált adatok pontosságának ellenőrzése
- Biztonsági mentések tesztelése

**Negyedévente:**
- NAV kapcsolat teljes tesztelése
- Biztonsági beállítások felülvizsgálata
- Teljesítmény optimalizálás

### 8.2 Kapcsolat

További segítségért vagy kérdések esetén:

- **Dokumentáció**: `PRODUCTION_SETUP.md`
- **Hibajelentés**: GitHub Issues
- **Technikai támogatás**: Lépjen kapcsolatba a fejlesztőcsapattal

---

*Ez az útmutató a NAV Online Számla API v3.0 specifikáció alapján készült. A NAV API változásairól és frissítéseiről tájékozódjon a hivatalos NAV dokumentációban.*
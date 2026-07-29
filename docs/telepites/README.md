% Telepítési és üzembehelyezési dokumentáció
% Krüpl Zsolt, Marton József
% 2020-2023

# Telepítés

## Előkövetelmények

 - Python 3.7
 - Debian 10
 - PostgreSQL 11.7
 - Apache2 httpd
 - NodeJS 14
 - csomagok:
   `postgresql`
   `python3 python3-virtualenv python3-pip libapache2-mod-wsgi-py3`
 - telepítési könyvtár, a git tartalma kerüljön ide (alapértelmezett): `/var/www/tudomanymetria-riportkeszito/`


## PostgreSQL adatbázis létrehozása

`postgres` userként

```shell
$ createuser tesztuser -P
## opcionálisan:
##  -O owner-user-neve
##  -T template0 # ha az encoding miatt nem sikerül a createdb hívás
$ createdb tudriport -E UTF8 -l hu_HU.UTF-8
```

Az adatbázis sémát a Django migrációs folyamat hozza létre ill. tartja karban.

Adatbázis séma dump adatok nélkül, azaz "pg_dump -s".

```shell
pg_dump --no-owner --schema-only -U user -d tudriport
```

## Konfiguráció

 Másoljuk le a `tudriport/config.local.json.sample` fájlt `tudriport/config.local.json` névre és töltsük ki a `tudriport/common/config.py` fájlban található szerkezet szerint a felülbírálni kívánt kulcsokat.

  - Az eredő konfigurációt tesztelhetjük: `python3 -m tudriport.common.config --print`
  - Egy konfigurációs kulcsot lekérdezhetünk (pl. shell scripthez): `python3 -m tudriport.common.config --key db.SQLHOST`

## Apache 2.4 webszerver beállítása

1. A `/etc/apache2/conf-enabled/serve-tudomanymetria.conf` helyen az alábbi beállításokra van szükség:

```
# Python/WSGI processz definicio
WSGIDaemonProcess tudriport user=nobody group=nogroup home=/var/www/ processes=1 threads=5 python-path=/var/www/tudomanymetria-riportkeszito/riportkeszites-django/riport/ python-home=/var/www/tudomanymetria-riportkeszito/env

# Kliens disztribucios mappa
Alias "/tudriport/static" "/var/www/tudomanymetria-riportkeszito/riportkeszites-django/riport/static_collected"
Alias "/tudriport" "/var/www/tudomanymetria-riportkeszito/riportkeszites-angular/dist/riportkeszites-angular"

# Backend API URL
WSGIScriptAlias /tudriport-api /var/www/tudomanymetria-riportkeszito/riportkeszites-django/riport/riport/wsgi.py

# API utvonal és WSGI processz group hozzarendeles + Shibboleth
<Location /tudriport-api>
WSGIProcessGroup tudriport
AuthType shibboleth
ShibRequestSetting requireSession Off
Require shibboleth
</Location>

# Hozzaferes engedelyezese es az Angular szamara a .htaccess engedelyezese (AllowOverride)
<Directory /var/www/tudomanymetria-riportkeszito/riportkeszites-django/riport/static_collected/>
  Require all granted
</Directory>
<Directory /var/www/tudomanymetria-riportkeszito/riportkeszites-angular/dist/riportkeszites-angular>
  Require all granted
  AllowOverride All
</Directory>
```

2. Engedélyezzük a WSGI modult és a rewrite modult: `a2enmod wsgi rewrite`
3. Indítsuk újra a webszervert: `service apache2 restart`


## Egyedi URL használata

Ha nem a `/tudriport` ill. `/tudriport-api` alatt érhető el az instance, akkor az alábbi lépéseket kell máshogy csinálni. Erre pl. a dev gépen szükség van, ahol több instance él egymás mellett:

1. A fenti Apache beállításokat duplikálni kell a megfelelő URL útvonalak és fájlrendszer path-ok használatával
2. Backend API path: a `root_url˙ állítandó át, l. `riportkeszites-angular/src/app/api/api.configuration.ts#L5`
3. Frontend build: az `ng build` során kell megadni a `--base-href=` paraméterben, l. `install/install.sh#L25`
4. Frontend static files: a `STATIC_URL`-t kell beállítani a `local.py`, `production.py` vagy közvetlenül a `base.py` helyen, l. `riportkeszites-django/riport/riport/settings/base.py#L206` . A központi konfigurációban, illetve preferáltan annak helyi kiegészítésében (`config.local.json`) a `django.settings_module` kulcs adja meg, hogy melyik konfigurációt használja a Django.

## Adatfrissítő szervíz konfigurációja és felügyelete

Az adatfrissítést az `input_queue`-ba bekerült feladatok alapján az `input_queue_processor` Django panacs végzi, ami `screen` terminal multiplexerben fut.

### Konfiguráció

Ezt [User-scope systemd szervízként](https://wiki.archlinux.org/title/systemd/User) telepítjük az alkalmazás futtató user accountja alá.

Az alábbi leírás során feltételezzük, hogy:
 - alkalmazás futtató user: `tudriport`
 - telepítési könyvtár (git repository root): `/var/www/tudomanymetria-riportkeszito`

`root` felhasználóként:

1. screen telepítése: `apt-get install screen`
2. systemd/User szervíz engedélyezése: `loginctl enable-linger tudriport`

`tudriport` felhasználóként:

3. lépjünk a telepítési könyvtárba: `cd /var/www/tudomanymetria-riportkeszito`
4. ellenőrizzük a szervíz paraméterezését a `utils/input_queue_processor__service.sh` fájlban
5. ha nincs ilyen, hozzuk létre a felhasználói systemd szervíz könyvtárat: `mkdir -p ~/.config/systemd/user/`
6. másoljuk be a szervíz leíró fájlt és szükség szerint módosítsuk: `cp install/tudriport-iqp.service ~/.config/systemd/user/`
7. engedélyezzük a szervízt: `systemctl --user enable tudriport-iqp`
8. indítsuk el a szervízt: `systemctl --user start tudriport-iqp`, vagy indítsuk újra a gépet hogy lássuk, elindul-e automatikusan

### Felügyelet

`tudriport` felhasználóként:
 - a szervíz állapotának lekérdezése: `systemctl --user status tudriport-iqp`
   itt ha `Active: active (running)` állapotot látunk, akkor fut, ha mást, pl. `dead`, akkor az nem jó
 - a szervíz termináljának a megjelenítése: `screen -r`

 - szervíz indítás: `systemctl --user start tudriport-iqp`
 - szervíz leállítás: `systemctl --user stop tudriport-iqp`

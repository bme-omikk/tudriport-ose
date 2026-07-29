% Tudománymetriai riportkészítő követelmény-specifikáció
% Krüpl Zsolt, Kollár Zsolt, Marton József
% 2018. január 25.


Bevezetés
=========

A rendszer célja, motivációja
-----------------------------

Az [MTMT] nyilvános közlemény- és idézőközlemény nyilvántartása alapján előre definiált és
ad-hoc riportok elkészítését (intézményi és egyéni összesítő pontozásokat) támogató rendszer elkészítése.

A cél, hogy az igényfelmérés alapján jól definiált szempontok, ún. dimenziók értékeinek
tetszőleges kombinációja szerint lehessen szűrni, majd különböző metrikákat számolni és listázni.

Fontos kiemelni, hogy a rendszer nem validálja/ellenőrzi az adatok hitelességét: ezek hitelességéért a szerzők felelősek, a rendszer csak 
számol az adatokkal.

Célközönség
-----------
- BME - Karok, EHBDT, Egyetemi statisztikák 
- ODT
- Akadémia
- Külső

Alapkoncepció
-------------

Alapvető szempont, hogy a lekérdezési lehetőségek rugalmasak és gyorsak lehessenek.
Ennek érdekében az MTMT-kapcsolat nem online. Helyette a rendszer előfeldolgozott adatokat
tart karban, és a lekérdezéseket saját, erre a célra tervezett adatbázisából szolgálja ki.

Funkcionális követelmények
==========================

Riportkészítési funkciók
------------------------

A rendszer beépített és ad-hoc riportok elkészítését teszi lehetővé.
A riportolás alapja: az egyes közleményekre vonatkozó mértékek és azok súlyozott értéke,
melyet az úgynevezett pontozófüggvény számít ki.

A pontozófüggvény eredménye kétféle bontásban érdekes:

 - közleményenként, pl. egy személy munkássága a pontozás eredményével annotálva
 - közlemény-kategóriánként aggregálva

Az aggregált lista mindig kibontható annak érdekében, hogy ellenőrizni lehessen, hogyan jött ki az adott aggregáció eredménye.

Az aggregáció lehet:

 - `sum()`: a súlyozott vagy súlyozatlan pontszám numerikus összegzése
 - `count()`: a kategóriába sorolt forrásközlemények száma
 - `count(distinct)`: a kategóriába sorolt különböző forrásközlemények száma

### Riport paraméterek

Az egyes beépített riportok meghatározhatnak paramétereket, amelyeket a riport lekérdezése előtt meg kell adni. Ezek a paraméterek lehetnek kötelezőek vagy opcionálisak.

A paraméterek értelmezését mindig az adott riport specifikációja tartalmazza.

Példa. Riport paraméterek lehetnek:

 - időintervallum-átfogás: év felbontású *tól-ig* dátum, a riport készítésekor csak az adott időszakban keletkezett idézőközleményeket ill. forrásközleményeket kell figyelembe venni. Zárt intervallum, amelynek valamelyik vége ha nincs megadva, akkor azon az oldalon nincs szűrési feltétel.
 - vizsgált szerző: pl. PhD pontszámításkor az a szerző, akinek a szempontjából a pontozást készítjük. Az ő szempontjából számítjuk a súlytényezőt, vagy vizsgáljuk, hogy első szerző-e stb.
 - témavezetők listája (opcionális): VIK PhD pontszámításkor a jelölt szerzői részesedését a felsorolt személyek részesedését levonva kell korrigálni. Ha nincs megadva, akkor nem kell korrigálni.

### Súlyozási lehetőségek

Az egyes közleményekre vonatkozó mértékek súlyozhatóak pl. szerzői részesedéssel.

A súlyozás mértékenként különböző lehet, és a pontozófüggvény határozza meg.

### Mértékek

 - közlemény mennyisége
    - alapvetően 
 - kapcsolódó idéző közlemények évenként, az alábbi szempontok szerint számolt mennyiség  
   Fel kell jegyezni az érintett idézők azonosítóját is annak érdekében, hogy a számok validálhatók legyenek.
    - függő/független/nem tudjuk
    - WoS-ban szerepel
    - Scopus-ban szerepel
    - idézés éve
 - impact factor

### Attribútumok

Ezek egy része dimenziókulcs, mások közvetlenül eltárolt értékek lehetnek a közleményrekordban.

 - közlemény besorolás
 - közlemény jelleg
 - közlemény MTMT azonosítója
 - Szerző: multi
    - részesedés
    - sorszám adott típusú szerzők között  
      csak az MTMT-ben azonosított szerzőket tartjuk itt nyilván, ezért kell az alábbi két flag is:  
      első szerző? true/false  
      utolsó szerző? true/false
    - szerzőség fajtája: szerző vagy szerkesztő
    - szervezeti hovatartozás (egyetlen sapka, amiben a közleményt írta)
 - közlemény megjelenés éve
 - nyelv
 - lektorált
 - sorozati befoglaló
 - kiadás helye
 - publikáció hossza
 - WOS adatbázisban szerepel
 - Scopus adatábázisban szerepel
 - Könyvtáros jóváhagyta?

Az egyes attribútumok pontosítása az *MTMT adat - XML leképzés (mapping rules)* c. mellékletben szerepel.

### Dimenziók

 - szervezeti felépítés (hierarchikus dimenzió)
 - szerzők listája (MTMT1 és MTMT2 id számára is legyen mező)
 - közlemény besorolása (hierarchikus dimenzió: altípus, típus)
 - közlemény jelleg, benne flag: tudományos-e?
 - könyvtáros jóváhagyási státusz: nem/igen (az igen tovább bontható: érvényesítette, hitelesítette, de az MTMT1 XML exportban nem látszik a különbség)
 - hely, benne flag: magyar/külföldi/nemtudjuk
 - nyelv: hierarchikus dimenzió, melynek szintjei
    - magyar/idegen nyelvű
    - magyar/angol/német/francia/orosz/kínai/egyéb idegen nyelvű
 - sorozati befoglaló mű (másnéven: ISSN-nel ellátott befoglaló mű: folyóirat, könyvsorozat stb.)
    - flag: folyóirat: igen/nem; lektorált: igen/nem/nemtudjuk
    - két ISSN is tartozhat egy folyóirathoz: a nyomtatott és az elektronikus változatnak külön ISSN-je van.
    - a folyóiratokon a lektoráltság flag beállítása folyamatos az MTMT-ben. Amikor ezt frissítjük a mi rendszerünkben pl. az 1234-5678 ISSN-ű folyóiratra, onnantól az összes abban megjelent cikknél már az új lektoráltság flag szerint kell értékelni az összes, abban megjelent közleményt.


### Beépített riportok

A beépített riportok listája bővíthető. Alapvetően kétféle riporttípus van:

 - listás: pl. egy PhD jelölt publikációs pontozó listája
 - táblázatos: pl. egy tanszék dolgozói szintű publikációs teljesítménye
 
A kapcsolódó pontszámítási táblázatok jelen specifikáció mellékletében szerepelnek.

### Ad-hoc riportolás

A rendszer biztosítson lehetőséget közlemények szűrésére a dimenziók és hierarchikus dimenziók mentén.
A szűrés eredménye legyen listásan megjeleníthető, illetve
a szűrés eredménye a dimenziók éstékei ill. érték-hierarchiái mentén csoportosíthatók.

A rendszerben definiált pontozófüggvények a szűrt eredményekre alkalmazhatók, és csoportosítva illetve elemi szinten is megjeleníthető a pontozás.

Riport exportálási funkciók
---------------------------

Archiválás és más rendszerekkel történő kommunikáció céljából a riportok böngészőben, az alkalmazás keretein belül történő megjelenítése mellett támogatni kell:

 - más weboldalakba beágyazható, minimális ún. *HTML snippet* lekérdezést,
 - standalone HTML exportot (pl. a riport pillanatfelvételének archiválása céljából), amely külső elemek (stíluslap, képek, szkriptek stb.) nélkül, önmagában visszaadja az eredeti információtartalmat
 - géppel olvasható exportot a riport adattartalmáról  (JSON, XML vagy ahhoz hasonló félstrukturált formátumban)


Pontozófüggvény
===============

Az egyes pontozási rendszerek meghatároznak kategóriákat, és ezeknek a kategóriáknak a mentén számítanak ki mértékeket (adnak pontokat).

A pontozófüggvények lehetnek

 - mindenki számára elérhetőek
 - csak meghatározott felhasználók számára elérhető (tesztelési, fejlesztési célzattal)


Egy forrásközlemény kategorizálása
----------------------------------

Egy kategórián címkék sorozatát értjük. Egy riportban lehetséges kategóriák *prefix kód*ot alkotnak.

Példa. A BME éves statisztikai táblázatnál a 2016-os évre vonatkozóan ezek a következők:

 - (2016, összes közlemény)
 - (2016, jóváhagyott közlemény)
 - (2016, idéző)
 - (2016, független idéző)


Egy forrásközlemény vagy idéző közlemény *0, egy vagy több kategóriába* is tartozhat, pl. az előbbi példát folytatva egy *2016-ban megjelent, jóváhagyott forrásközlemény* a *(2016, összes közlemény)* és a *(2016, jóváhagyott közlemény)* kategóriákba tartozik, míg egy *2016-ban megjelent, nem jóváhagyott forrásközlemény* csak a *(2016, összes közlemény)* kategóriába tartozik.


Egy forrásközlemény pontozása
-----------------------------

Egy forrásközlemény pontozása a *P(k, p) -> (C, a, s)... * függvény, ahol:

 - *k* a forrásközlemény rekord, amelyet pontozunk,
 - *p* a futtatott riport paraméterek,
 - *C* egy kategória,
 - *a* a súlyozatlan pontszám,
 - *s* a súlytényező,
 - a pontozófüggvény 0, egy vagy több *(C, a, s)* hármast adhat eredményül, melyek között *C* nem ismétlődhet.

Egy közlemény adott *C* kategóriába tartozó súlyozott és súlyozatlan pontszáma rendre *a \* s* és *a*, ha *(C, a, s)* szerepel a pontozófüggvény eredményében; egyébként 0.

### Súlyozási lehetőségek

A súlyozást (súlytényezőt) a pontozófüggvény határozza meg. Az itt szereplő példa csupán egy illusztráció.

Példa:

 - A forrásközlemények pontszámánál a leggyakoribb súlyozás a szerzői részesedéssel történő súlyozás.
 - Szintén gyakori a szerzők illetve szerkesztők számával történő osztás is (egyenlő hozzájárulás feltételezése)
 - A szerzői részesedés esetén speciális szabály lehet, hogy bizonyos esetekben a vizsgált személy témavezetőjének
szerzői részesedése nélkül kell a vizsgált személy részesedését kiszámolni, azaz ha
egy közleményben a vizsgált személy szerzői részesedése *r(v)*, a témavezetőjének részesedése *r(t)*, akkor
a vizsgált személy *korrigált részesedése = r(v) / (1-r(t))*.  


Adatforrás
==========
Az riportkészítő két forrásból dolgozik:

 1. Szerzői névsorok: az adminisztrátor felhasználótól származó CSV adatfile:
     - név
     - MTMT azonosító
     - súlyozás
     - beosztás (erősen korlátozott értékkészlet: oktató/doktorandusz) (opcionális)
     - témavezető(k) MTMT azonosítója (opcionális)

    A névsorok max 4-szintű, hierarchikus névvel azonosíthatók, melynek preferált használata rövidítéssel: egyetem, kar, tanszék, labor vagy csoport; Pl. `(BME, VIK, TMIT, DBlab)`, `(BME, GPK, PT, null)` vagy MTA esetén `(MTA, MTO)`. Ennek a célja, hogy a tanszéki névsorokat lehessen *rollup-szerűen*, kari névsorokként is használni.  
    **FONTOS:** A CSV bemeneti fájl adataink helyességét (súlyozás mértéke, beosztás) a felhasználó biztosítja.
    A rendszer minimális admin adattámogatát és vsszajelzés nyújt: pl. MTMT azonosítók validálása, Név-azonosító páros ellenőrzése alapján figyelmeztetés megjelenítése.
 2. A riportok közvetlen adatforrása a rendszer saját adatbázisa.
A rendszer a saját adatbázisát folyamatosan frissít az [MTMT] adataiból, illetve további, kiegészítő adatok bevitelére és karbantartására helyben biztosít lehetőséget.
 3. Folyóirat-osztályozás: az adminisztrátor felhasználótól érkező CSV, amivel osztályozni lehet a folyóiratokat, pl. A/B/C/D
     - ISSN
     - eISSN
     - Folyóirat neve
     - Folyóirat rövid neve
     - hazai/nemzetközi (boolean, lehet NULL)
     - osztályozás

    A folyóiratlisták max 2 szintű, hierarchikus névvel azonosíthatóak, melynek preferált használata: szervezet rövid neve, lista azonosítója. Pl. (MTA-GJO,ÁJB) vagy (MTA-GJO,GMB).

MTMT-kapcsolat
--------------

Az MTMT-kapcsolatot közleményenkénti lekérdezéssel kell megvalósítani. A jelenlegi MTMT1 rendszerhez és a jövőben várhatóan induló MTMT2-höz kapcsolódó illesztőt is el kell készíteni.

Résztelesen ld. az [MTMT adatforrás leírása](../adatforrasok/mtmt) anyagban.


Közlemények feldolgozási sora
-----------------------------

A rendszer saját adatbázisának frissítését közlemény-alapú lekérdezéssel, szakaszosan végzi.
Ennek érdekében egy sort kezel, ahol a frissítendő közlemények MTMT-azonosítója elérhető.
Később kerül meghatározásra, hogyan történik ennek a sornak a táplálása.

Az, hogy egy közleményrekord azonosítója bekerült a frissítendő sorba, nem feltétlenül jelenti azt,
hogy a rendszer saját adatbázisában változtatás fog történni. Előfordulhat ugyanis, hogy a közlemény olyan adatában volt változtatás,
ami a rendszerben szereplő lenyomatát nem érinti (pl. elírás javítása a címben).
A rendszer saját adatbázisában akkor és csak akkor jön létre új verzió, ha a forrásrendszerből jövő rekordban olyan változás volt,
aminek következtében a rendszerben szereplő lenyomat módosul.

A sor kezelésére kidolgozandó stratégiához figyelembe kell venni, hogy az MTMT-ben
adatkarbantartás ill. migráció (együtt: karbantartás) alkalmával olykor 1.000.000 nagységrendű közleményrekord is módosulhat,
amely sokszor nem érinti a riportolási dimenziókat és mértékeket.
Ezért célszerű olyan sorkezelési stratégiát kidolgozni, ami ilyen esetekben is elfogadható késleltetés mellett feldolgozza a nem karbantartás során módosult vagy létrejött rekordokat. Ehhez nem áll rendelkezésre sem módosítási időbélyeg, sem arra vonatkozó információ, hogy karbantartás vagy nem karbantartás során módosult a közleményrekord.

Beérkező állományok tárolása
----------------------------

Az egyes adatforrásokból érkező állományokat rendszer fájl formájában is mentse el a feldolgozás időbélyegével együtt, strukturált könyvtárszerkezetbe.
Az így elmentett fájlok fájlnevükben hordozzák az állomány adatforrás-beli azonosítóját (pl. közelmény XML forrásrendszer neve és közlemény azonosító).


A tárolás célja a hibakeresés.


Verziókezelés, visszapillantás
==============================

A rendszer minden rekordját verziókezelve kell tárolni.

Lehetőséget kell adni arra, hogy a rendszerből a közlemény és idézőadatok adott időpontban érvényes változata kinyerhető legyen.
A pontozófüggvény mindig az ennek az időpontnak megfelelő adatokat kapja meg.

Nem-funkcionális követelmények
==============================

Hozzáférés
----------

A rendszer felhasználói felülete mind megjelenésében, mint technikailag korszerű weboldalként érhető el, titkosított https felületen.

Az egyes riportok `HTTP GET` kéréssel, állapotmentesen linkelhetők strukturált URL segítségével.
Ennek érdekében a böngésző URL sávjában mindig az adott riportra vonatkozó URL elérhető.

### Authentikáció (login kezelés)

eduID segítségével, a magyar akadémiai szférához kapcsolódó emberek részére engedélyezett a bejelentkezés.

Lehetnek nyilvános oldalak is a rendszerben.


### Authorizáció (jogosultságkezelés)

Intézményi szintű jogosultságkezelésre van szükség.

Adott intézményen, így pl. BME-n belül nem szükséges további jogosultságkezelés.
Amint több egyetem/résztvevő kerül be a rendszerbe, akkor már minden felhasználó csak a saját intézményének adataihoz férjen hozzá. Pl. BME és az MTA MTO között jogosultságok szempontjából különbséget kell tenni.

Bizonyos modulokhoz szükséges lehet IP tartományok szerint fehérlistával korlátozni.


## Adatvédelem

Az adatok továbbítása titkosított https csatornán történnek. Minden adathoz csak az arra jogosultak férhetnek hozzá megfelelő azonosítás után.

Az egyes anyagokhoz való hozzáférés az URL ismeretében sem kerülheti ki a jogosultságkezelést.

## Naplózás (auditálás)

Szükséges feljegyezni, hogy ki, mit és mikor kérdezett le a rendszerből.

A lekérdezés eredményét nem kell tárolni, hiszen a rendszer verzókezelve tárolja a tiportok alapjául szolgáló adatokat.

## Rekordok technikai metaadatai

A rendszer minden táblájának minden rekordjában a többi mezőtől függetlenül szerepelnek az alábbiak, amit lehetőség szerint minél alacsonyabb szinten kell kezelni (pl. DBMS trigger / default érték):

 - numerikus elsődleges kulcs
 - rekord beszúrási időbélyege és a beszúrást végző user (adatbázis vagy alkalmazás user)
 - rekord módosítási időbélyege és a legutóbbi módosítást végző user (adatbázis vagy alkalmazás user, beszúráskor megegyezik a beszúrási adatokkal)

Az érvényesség kezdezdete/vége jellegű verziókezelés által nem érintett táblákban továbbá szerepel:

 - rekord logikai törlésének időbélyege

A rendszer saját funckciói rekord DBMS szintű törlését nem végezhetik.

A rendszer minden nem history tábláján DBMS trigger szinten history kezelés történik, amely a beszúrási eseményen kívül minden rekord-módosítást rögzít az alábbi metaadatokkal:

 - a history bejegyzés elsődleges kulcsa (`h_id`)
 - a history bejegyzés keletkezésének oka (`h_action`: (U)pdate/(D)elete)
 - a history bejegyzéshez kapcsolódó adatbázis user (`h_user`)
 - a history bejegyzés keletkezésének időbélyege (pl. `h_date`)

## Hiba és figyelmeztetés napló

A rendszer működése (adatforrás beolvasása ill. üzemeltetés) során keletkező hibákat szöveges fájlba, sor-orientáltan naplózni kell a hiba szintjét, időpontját és a művelet azonosításához szükséges adatokat.

Adatforrás beolvasása során fellépő figyelmeztetés vagy hiba (l. mapping rules) vagy nem várt hiba esetén az adatforrás nevét és a rekord azonosítására alkalmas adatokat naplózni kell. Ilyenkor a beolvasott állomány mindenképpen mentendő.

A naplózáshoz havi logrotate konfiguráció szükséges, korlátozás nélküli napló megtartási idővel.


## Adatmennyiség

 - kezelt közleményrekordok mennyisége: 10.000.000 közlemény
 - napi frissítés: 20.000 közlemény 
   Megjegyzés: ezt az MTMT1 teljesítménye korlátozza ilyen értékre. A rendszerben a paraméternek hangolhatónak kell lennie.
 - egy személy közleményeiről szóló riport által érintett adatok: 1.000 közlemény
 - csoportos áttekintő riportok esetén:
    - átlagos közleményszám: 100/személy
    - érintett személyek száma: tipikusan 50-500 közötti, de akár 5000 is lehet (teljes egyetemi listák)

## Adatfrissesség, késleltetés

A rendszer az MTMT-ből a *Közlemények feldolgozási sora* c. szakaszban szereplők szerint megkapott egyedi frissítési eseményekre legfeljebb
1 napos válaszidővel reagáljon.

A karbantartás eredményeképpen érkező tömeges frissítési eseményekre best effort jelleggel, az *Adatmennyiség* részben szereplő ráta szerint kell reagálni.

## Számított értékek ellenőrzése

Minden értéknek validálhatónak kell lenni, ennek érdekében az adatbázisban tárolni kell a közlemények és idézők
forrásrendszert (MTMT-beli) azonosítóját, és a pontozásokban/listákban kinyerhetőnek kell lenni, hogy az adott pontszám
mögött melyik közlemények és idézők vannak.

## Válaszidő követelmények

A pontos hardver ismeretének hiányában a válaszidő követelményekre annyi a követelmény, hogy:

 - egy személy közleményeiről szóló listák 10 másodperces válaszidővel lekérdezhetőek legyenek
 - a csoportos listák lekérdezése: ha a prototípus-tesztek szerint tipikusan meghaladja a perces nagyságrendet, akkor folyamatjelzőt kell alkalmazni

## Üzemeltetési környezet

### Programkód verziókezelés és hibajegykezelés

A programkód verziókezelése git rendszerben történik, hibajegykezeléssel.

### Telepítés

A telepítés egyetlen `git pull` művelet, majd opcionálisan egy automatizálható build procedurával történik.

### Szerveroldali környezet

A szerverkörnyezet Debian Linux 9 stable amd64.

Törekedni kell arra, hogy amit lehet, azt a Debian csomagkezelőjén keresztül, az adott Debian verzióból lehessen telepíteni.

Webszerver: az Apache httpd preferált, ettől egyeztetés szerint el lehet térni.

Adatbázis-kezelő rendszer: PostgreSQL vagy MariaDB. PostgreSQL preferált, de egyeztetés szerint ettől el lehet térni.


Fogalomtár és rövidítések jegyzéke
==================================

 - dimenzió: olyan, tipikusan kategória-jellegű jellemző, ami szűrési ill. lekérdezési szempont alapját képezheti
 - forrásközelmény: az az eredeti közlemény, amelyet a kutató munkájának eredménye.
 - idéző közlemény: a forrásközleményre hivatkozó mű.
 - kategória: címkék sorozatát értjük. Egy riportban lehetséges kategóriák *prefix kód*ot alkotnak.
 - közlemény: kétféle lehet: *forrásközlemény* ill. *idéző közlemény*.
 - mérték: numerikus jellemző, amelyen számításokat lehet végezni tipikusan aggregáció alkalmával (súlyozott vagy nem súlyozott összegzések, statisztikai jellemzők atb.)
 - MTMT: Magyar Tudományos Művek Tára, az országos tudományos bibliográfiai adatbázis, jelen rendszer elsődleges adatforrása
 - MTMT-azonosító:
    - közleményé: MTMT1-ben jelenleg 7 vagy kevesebb jegyű, numerikus azonosító;
    - kutatóé: az MTMT1-ben jelenleg 8 vagy kevesebb jegyű, numerikus azonosító; 
    - MTMT2-ben szintén numerikus azonosítók vannak, de a hossza egyelőre ismeretlen
 - riport: itt: adott adathalmazra (pl. egy tanszék vagy egy kutató közleményei) adott beállítások szerinti súlyozással és adott granularitás mellett elkészített eredménylista. Ez a rendszer végterméke, tipikusan táblázatos vagy más, strukturált formában megjeleníthető. 
 - súlyozási függvény: a közlemény egy mértékének és különböző jellemzőinek (pl. terjedelem, nyelv) kombinációjához numerikus értéket rendelő függvény.
 - súlyozási függvény-készlet: a közlemény mértékeihez tartozó súlyozási függvények elnevezett halmaza.



[MTMT]: https://www.mtmt.hu

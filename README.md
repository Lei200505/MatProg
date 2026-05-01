# BudapestWoo

A projekt a BKK járatain egy útvonaltervező. Az ismert Budapest GO alkalmazás egyszerűsített kevésbé optimalizált változata.
A program Budapest tömegközlekedési hálózatán, BKK, segít útvonalat tervezni GTFS adatok alapján. 
A projekt az OpenData Portál tervezett menetrendi adatait használja:
https://shorturl.at/X8C9O

## Használat
1. Töltsd le a fenti linkről a ZIP fájlt (budapest_gtfs.zip)
2. Csomagold ki a projekt mappájába
3. Nevezd át vagy helyezd át a mappát ide: budapest_data
4. Futtasd a graph.py és a night_graph.py fájlokat (ezek eltarthatnak egy ideig kb 1-2perc)
- (1.-4 lépések akkor szükséges csak, ha friss adatokkal szeretnéd használni)
5. A program inditásához szükséges fájl: ui.py
- Ezek után már elég csak ezt a fájlt futtatni ha többször is szeretnéd használni


## Funkciók
A program alapvetően egy leggyorsabb utat keres két megálló között az indulási időponttól kezdve, ehhez a megfelelő tervezett menetrendet használva és feltételezve, hogy a felhasználó nem szeretne túlságosan sokat sétálni. Ehhez be kell állítani a kiinduló állomást és a célállomást és a indulási időpontot két legördülő menü segítségével. A tervezés gombra kattintva egy animáció jelenik meg Budapest térképéről a megtalált legrövidebb úttal. (Ezt ne próbáljuk meg kiikszelni, mert az animáció ígyis végbe fog menni). Ezek után megjelenik ennek a tervnek egy statikus rajza és egy részletes írott útvonalterv is.

- térkép/éjszakai térkép: a két gomb megnyomásával a megfelelő térképet meg lehet nézni amivel dolgozik az algoritmus

- Nem talált útvonal: előfordulhat, hogy túl későn indulnál el egy megállóba ahova vagy csak nagyon sok sétával vagy csak nagyon sokára érnél oda, ilyenkor azt ajánlja, hogy hamarabb indulj el

-Easter egg: a Maglódi Auchan megálló az egyetlen olyan megálló ahova, ha éjfélhez elég közel akarsz indulni, akkor azt az üzenetet kapod, hogy a megálló nem is létezik (ennek az oka, hogy a megállóhoz legközelebbi másik megálló 1km-es távolságon kívül van így az algoritmus szerint) 

# Fájlok tartalma

## graph.py, night_graph.py

### Dependenciák
- numpy és pandas fogja a nagy mennyiségű GTFS adatok kezelni.
- networkx fogja a felípetett gráfhoz biztosítani az alapvető adatstruktúrát biztosítani. MultiDiGraph-ot, azaz irányított, nem egyszerű gráfot építünk. A járatok és megállók információit az él- és csúcsattribútumként tároljuk.
- SciPy.spatial: cKDTree modul segítségével találjuk meg közel konstans időben az egymáshoz közeli megállókat.
- pickle: .pkl formátumban mentjük a gráfot a gyors, bináris adatolvasáshoz.
- json (már nem használt): ezzel emberek számára is olvasható formátumban menthető a gráf
- os: filekezelés.

### Bevezetés
A gráf felépítése a graph és night_graph fájlokban történik meg. A kód a teljes GTFS adatbázisból egy networkx gráf objektumot hoz létre, majd azt .pkl formátumban menti a gyors megnyitásért. Megjegyzendő, hogy eredetileg .json formátumot használtunk, ami bár kedvezőtlenebb betöltési idejű volt, de ember számára is olvasható, és így egyszerűbbé tette a debug-olást, valamint a lentebb részletezendő, legrövidebb út keresésére legalkalmasabb adatstruktúra kialakítását.

Az adatbázis legnagyobb hiányossága az átszállások megvalósítása. Ha kizárólag a GTFS adatokból dolgoznánk, akkor a megállok kizárólag a beléjük, és belőlük futó járatokkal közelíthetőek meg, és így az átszállás nem lehetséges. A megoldást erre a közeli megállók átszálló élekkel való összeköttetése biztosítja, melynek működését az alábbiakban részletezzük. Ennek a konstrukciónak a szükségességét a Deák Ferenc tér jól illusztrálja: közel 40 megálló tartozik ehhez a csomóponthoz, átszálló élekkel nem lehetne a 3-as metróról a 9-es buszra szállni.

A két program gyakorlatilag identitikus, főleg beállításbeli különbségek adódnak. Azért van szükség külön éjszakai gráfra, mert az adatbázis éjfélkor értelemszerűen abbahagyja a járatok listázását, és így az éjfélhez közel, de még azelőtt utak nem érnek céljukba. Ezen túl, tekintve, hogy az éjszakai járatok ritkábban fedik le a hálózatot, távolabbi pontok közötti átszállóélek behúzását is engedélyezzük.

### __init__

Az inicializáló függvény létrehozza megadott mappában elhelyezett a legfontosabb adatforrásokat. Ezek a következők.
- stops.txt: Ez a hálózat megállólistáját tartalmazza. A megállót egy egyedi azonosítóval látja el, eltárolja a nevét, hosszúsági és szélességi koordinátáit. A Google egyébként további adatok, mint például szülő megálló (csomópontok modellezésére) eltárolására is biztosít lehetőséget, azonban ezt a BKK nem tölti, ezért is van szükség átszálló élekre.
- routes.txt: Ez a hálózat járatait listázza. Egyedi azonosítóval látja el a járatot, valamint hozzárendeli a járat nevét, mely két végállomás között közlekedik, valamint megadja a járat típusát: metró, villamos, busz, stb.
- trips.txt: A routes.txt-nél granulárisabb adat. Tartalmazza egy adott járat minden további viszonylatát, azaz leírja, hogy egy melyik végállomásról, mikor indul el, és ezt ellátja egy egyedi azonosítóval.
- stop_times.txt: A leggranulárisabb, és egyben a gráfépítéshez legfontosabb adat. Ez már a trips.txt-ben definiált viszonylatokhoz rendeli hozzá azok konkrét megálló szekvenciáját, valamint a megállókba való érkezés és az onnan való indulás idejét.

### time_from_str

Ez a függvény a GTFS által használt "HH:MM:SS" formátumból konvertál egy teljes időtömböt másodpercekre. A program során mindig 00:00:00-tól eltelt másodpercekben számolunk. Ha egy út például 23:30:00-kor indul, és éjfél után záródik, akkor engedjük, hogy túlcsorduljon 86400-on ez a számoló, éppen ezért van szükség az éjszakai gráfra, hogy ezeket az utakat is eltároljuk.

### edge_list

Ez a függvény a legcentrálisabb eleme ennek az osztálynak. Feldolgozzuk az __init__-ben definiált adatokat egy járatok viszonylatait tartalmazó éllistába, melyből aztán gráfot építünk.  Tekintsük a konstrukció menetét.

1. Először a stop_times-ot rendezzük viszonylatszám (trip_id) és megálló szekvencia szerint. Ezzel olyan pandas df-et kapunk, amelyben az egymást követő adatsorok egy konkrét jármű által érintett megállókat listázza.
2. Ezeket viszonylatszám szerint csoportosítjuk, majd az egyes csoportokon végig megyünk (egy csoport itt például a 7:00-kor induló 75-ös trolibusz megállószekvenciája.)
3. Az érintett megállókon végigmegyünk, majd egy élbe az alábbi adatokat tároljuk:
    - from_stop: melyik megállóból indul az adott él
    - to_stop: melyik megállóba megy az adott él
    - departure_time: mikor indul el az adott megállóból
    - arrival_time: miikor érkezik meg az adott megállóból
    - trip_id: melyik az a viszonylat azonosító, ami szerint az adott csoportot vizsgáljuk
4. Az így konstruált éleket egy újabb pandas df-be rakjuk.
5. Most rengeteg él van: minden viszonylatnak külön, ez nyilván életszerűtlen. Ezért összevonjuk a viszonylatokat járatok szerint csoportosítva (ezért kellett a korábbi lépésben az élbe viszonylatszámot tárolni, itt eltűnne ez az adat)
6. Ezek után csoportosítjuk az éleket from_stop, to_stop, route_id szerint, valamint beleírjuk az adott él járatának típusát (ez majd a kiírásnál hasznos, hogy lássuk melyik él metró, melyik busz, stb.). Ezzel most minden járatnak, minden általa érintett megállóköznek van egy éle. Ez sok párhuzamos élet eredményez (pl. Keleti és Huszár utca között fut él 5, 7, 8, 107, 110, 112 buszoknak saját éle), de jól diszkretizálja a járatokat a gráf már egy korai stádiumában.
7. Meghívjuk az átszállóéeleket legeneráló transfer_edges metódust, majd ezeket is beépítjük az éllistába, majd ezt visszadjuk.

Megjegyezzük, hogy ez még nem a végleges szerkezete a gráf éleinek. A végső cél az, hogy minden indulás minden élen viszonylatonként egy élattribútumban kerüljön.

###transfer_edges
A transfer_edges metódus átszálló éleket hoz létre az adott távolságú csúcspárok között. A nappali gráfban ez 200, az éjszakaiban 1250 méter.  A metódus szükségességét fentebb motiváltuk. Itt szükségünk lesz a SciPy.spatial cKDTree moduljára. Ez egy olyan adatstruktúra, ami egy 2-dim fát épít fel a stops.txt-ben definiált gömbi koordiniáták szerinti Euklideszi távolsággal, és így a közeli pontokat rendkívül gyorsan elérjük. Eleinte minden pontpárra ellenőriztünk távolságot, de ez O(n^2) idejével túlságosan lassúnak bizonyult.

Tekintsük a metódus lépéseit!
1. A stops.txt-ben adott koordinátákat egy numpy array-ben tároljuk, majd egy cKDTree-t építünk belőle. 
2. A távolságot egy egyszerű becsléssel definiáljuk: egy fok körülbelül 110 km, így a maximális távolság max_transfer_dist (200/1250) / meters_per_degree (110.000). Ekkor a cKDTree query_ball_point metódusa gyors elérést biztosít: minden pontra meghatározza a B(pont, max_dist)-ba eső pontokat.
3. Ekkor minden szomszédra megvizsgáljuk a távolságot np.linalg.norm segítségével, és előre definiált, konstans sebességgel (1.5m/s nappal, 1 m/s éjjel) átjárhatóvá tesszük őket.
4. Ugyanazzal az adatstruktúrával járunk el, mint a fenti éleknél:
    - from_stop: megálló, ahonnan sétálunk
    - to_stop: megálló, ahova sétálunk
    - route_id: TRANSFER <- jelezzük, hogy átszálló él
    - route_type: TRANSFER <- jellezük, hogy átszálló él
    - depratures: [(0, t, TRANSFER)] <- az indulása 0 időpontban lesz, t ideig megyünk át rajta konstans idővel.
5. Visszadjuk az így meghatározott átszállóéleket.

### graph

A fent konstruált éllistából létrehoz egy networkx MultiDiGraph objektumot, azaz egy párhuzamos élekkel is rendelkező irányított gráfot. 
1. Létrehozzuk a gráf objektumot.
2. Végigmegyünk a megadott éllistán, majd minden tekintjük az adott élen tárolt indulás listát. Ha éjszakai gráfot építünk, akkor a reggel 5:00 (18000 mp) induló járatokat felvesszük indulási idő + 1 nappal is az éjfélen túllépést beépítve.
3. Ezek után az indulási listából kiindulva felépítjük az alábbi éleket (u, v, **args):
    - u = from_stop
    - v = to_stop
    - key: ez technikai, nélküle valamiért hibát dobott
    - route_id: járat azonosítója
    - route_type: járat típusa (metró, busz, transfer, stb.)
    - departures: konkrét (indulás, átuzási idő, viszonylatszám) hármasok
4. Ezzel létrejöttek a gráf csúcsai, a megállók, melyeket a from_stop és to_stop révén stop_id azonosítja, erre rávetitjük csúcs attribútumként a megállók neveit is a későbbi könnyebb elérésért.
5. Végül eltávolítjuk az izoláltpontokat, és visszadajuk a gráf objektumot.

### save_graph
A létrehozott gráf objektumot elmentjük egy pickle bináris fileba. Alapértelmezetten a graph.py mappájába kerül. A networkx beépített nx.node_link_data metódusa egyszerűvé teszi a pickle-be írást, de hasonlóan json-be is kiírható a gráf. Ekkor egyszerűen
egy with open(file, rb) as f: data = pickkle.load(f) -> majd nx.node_link_graph(data) módon újra létrehozható gyorsan a gráf más fájlban.

## graph_viz.py

### Dependenciák
- networkx a gráf olvasáshoz és építéshez.
- numpy és pandas az adatkezeléshez
- pickle a gráfolvasáshoz
- matplotlib.pyplot a vizualizációhoz
- os a fájlkezeléshez

### Bevezetés
A graph_viz modul networkx MultiDiGraph objektumok matplotlib segítégével való kirajzolására képes. A teljes hálózaton túl a dijkstra.py modul által meghatározott legrövidebb utak s-fenyőjét is képes kirajzolni, ezzel az út vizualizálásával a GUI-ban is megjelenik funkcionális elemben.

### __init__
A kód futásához elegengedethetlen a stops.txt és routes.txt beolvasása. A stops.txt-ből a megállók elhelyezkedését, a routes.txt-ből az adott élek fajtáit térképezzük fel. Beolvassuk továbbá a gráfot is, de ezt csupán a teljes hálózat kirajzolásakor használjuk.



### viz
A teljes hálózat vizualizációjára alkalmas objektum. 
1. Először létrehozunk egy szótárat {stop_id: (stop_hosszúsági koord, stop_szelessegi koord)} alakban. Létrehozzuk a matplotlib figure-t.
2. Ezek után a gráf éleit, amelyet __init__-ben olvastunk be, leválógatjuk járat típus (route_type) szerint az éleket, majd a nx.draw_network_edges- segítségével a járatok szerint csoportosított éleket megfelelő színnel kirajzoljuk.
3. Végül kirajzoljuk a csúcsokat is és megjelenítjük a figure-t.

### get_edge_color
Az élekben eltárolt route_type attribútum segítségével kiolvassuk, hogy egy adott él milyen járműnek felel meg, majd visszadjuk a BKK által, az adott típusra alkalmazott színsémát: busz = kék, troli = piros, villamos = sárga, metró = fekete, hév = zöld, transfer = szürke, ha pedig nincs valamiért route_type (bár ez konstrukcióból adódóan nem lehetséges intakt adatbázis esetén) lila lesz.

Ez a metódus azután íródott, hogy a viz metódus meg lett volna írva, így abba nem volt értelme beleépíteni. Ezért csak a következő metódus használja.

### fenyo_viz
Ez a metódus a dijkstra.py outputjaként kapott legrövidebb utak start-fenyőjét kirajzolja, majd a szekvenciálisan feltűnteti a legrövidebb utat start és end pontok között.

1. Ehhez először a Dijkstra által megadott fenyo dictionary-t visszaalakítjuk egy nx.MultiDiGraph objektummá.
2. Megint beolvassuk a csúcsok helyeiet egy dictionary-be, mint viz-nél tettük, illetve létrehozzuk a plt.figure-t.
3. Kirajzoljuk szürkével a felfedezett éleket és csúcsokat, valamint a start és end csúcsokat nagyobb, színes módon vetítjük az ábrára.
4. Végül a dijkstra.py path legrövidebb útjából kiolvassuk a legrövidebb utat. A lépéseket egy for ciklusban, iteratívan építjük az utat, így "belelátunk" az algoritmus működésébe, a legrövidebb utat animáljuk.
5. Minden uv lépésre az útban meghatározzuk u-t, v-t, milyen és melyik járművön tette meg az u és v között, majd a get_edge_color segítségével megkapjuk a színét. 
6. Végül megfelelő színnel ábrázoljuk (felülírjuk, a 3.-ban szürkével kirajzolt út-élt), és megállítjuk az animációt plt.pause segítségével 0.2 másodperce lépésenként.
## dijkstra.py
- Feldolgozott gráf betöltése
- Megfelelő megállók és járatok betöltése
- Módosított dijkstra
    - Nappali vagy éjszakai gráf használata
    - Hiányos kimenet kezelése
    - Célállomásig tartó algoritmus (séta vagy buszjárat szerinti éleken haladva, járat rekonstruáláshoz szükséges adatok eltárolásával)
    - kimenetben rekonstruálni a megtalált legrövidebb utat 
- Útvonalterv szép kiíratásáshoz szükséges adatok
    - megfelelő járatok együttkezelése
    - idő konvertálása
    - szöveg létrehozása

## ui.py

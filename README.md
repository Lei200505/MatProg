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
A gráf felépítése a graph és night_graph fájlokban történik meg. A kód a teljes GTFS adatbázisból egy networkx gráf objektumot hoz létre, majd azt .pkl formátumban menti a gyors megnyitásért. Megjegyzendő, hogy eredetileg .json formátumot használtunk, ami bár kedvezőtlenebb betöltési idejű volt, de ember számára is olvasható, és így egyszerűbbé tette a debug-olást, valamint a lentebb részletezendő, legrövidebb út keresésére legalkalmasabb adatstruktúra kialakítását.

A két program gyakorlatilag identitikus, főleg beállításbeli különbségek adódnak. Azért van szükség külön éjszakai gráfra, mert az adatbázis éjfélkor értelemszerűen abbahagyja a járatok listázását, és így 
## graph_viz.py

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

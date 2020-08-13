### Projekt 1

Naprogramujte v jazyce C++/Python jednoduchou konzolovou aplikaci
(*bms1*), která bude realizovat demultiplexing a analýzu transportního
streamu vysílání digitální televize.

**Parametry programu:** 

    ./bms1 nazev_souboru.ts

**Funkce programu:** 

Načítá vstupní soubor (*nazev\_souboru.ts*), který obsahuje data
transportního streamu DVB-T vysílání. Výstupem aplikace bude soubor s
názvem *nazev\_souboru.txt*, která bude obsahovat detaily pro každý
vyextrahovaný kanál ze zpracovávaného transportního streamu.

**Obsah a formát výstupu**

-   Soubor bude obsahovat v hlavičce informace o zpracovávaném
    multiplexu získané z NIT servisní tabulky, detaily o jednotlivých
    programech získané z tabulek PAT a SDT, které budou doplněny o
    souhrnnou statistiku přenosové rychlosti pro všechny kanály, které
    patří k jednomu programu.
-   Každý řádek popisující jeden program multiplexu bude mít následující
    formát:

        PID-service_provider-service_name: <bitrate> Mbps

-   Jednotlivé řádky budou seřazeny podle hodnoty PID.
-   Bitrate počítejte na základě počtu paketů daného programu vzhledem k
    *celkovému počtu* paketů. Teda podle vzorce:

        bitrate_programu = pocet_paketu_pro_program/celkovy_pocet_paketu*bitrate_streamu

-   V případě, že program obsahuje více video/audio stop případně
    servisní informace, sčítejte bitrate všech těchto kanálu do společné
    hodnoty.
-   Přenosovou rychlost zaokrouhlete na 2 desetinné místa.

Příklad:

        Network name: SIT 1 CESKA TELEVIZE
        Network ID: 12345
        Bandwidth: 8 MHz
        Constellation: 64-QAM
        Guard interval: 1/4
        Code rate: 2/3
        
        0x0100-Ceska televize-CT 1 JM: 10.50 Mbps
        ...


**Další poznámky**

-   Při implementaci je možnost použít libovolnou knihovnu dostupnou na
    serveru *merlin.fit.vutbr.cz*, na kterém se budou vaše programy
    testovat.
-   Vzorový TS soubor naleznete [zde](./multiplex.zip).
-   Specifikace servisních informací transportního streamu DVB-T: http://www.etsi.org/deliver/etsi_en/300400_300499/300468/01.13.01_40/en_300468v011301o.pdf

Zdroj: https://www.fit.vutbr.cz/study/courses/BMS/public/proj2019/p1.html.cs


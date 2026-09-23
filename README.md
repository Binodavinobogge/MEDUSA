# MEDUSA 0.4.2

<<<<<<< HEAD
### Your network, within reach.

**MEDUSA** is a lightweight desktop application for Windows that puts your PC’s network activity within easy reach.

Designed to stay conveniently on your desktop, it helps you quickly check active connections, inspect open ports, identify the processes behind them, and close a connection or terminate its process when needed.

An ocean-inspired interface, an animated jellyfish, and an interactive radar make network activity easier to explore.

> **See what’s connected. Understand what’s running. Take action.**
=======
Interfaccia nativa PySide6 collegata al monitor psutil del progetto originale.

## Avvio su Windows

1. Chiudi la vecchia MEDUSA. Estrai **tutto** lo ZIP: questa versione usa la cartella **MEDUSA-0.4.2**. Non eseguirla dall’archivio.
2. Installa Python **3.10 o successivo, 64 bit**, se non presente.
3. Fai doppio clic su **AVVIA_MEDUSA.bat**. Il primo avvio crea `.venv` e scarica le dipendenze; richiede Internet. Gli avvii successivi usano questo ambiente.
4. Se Windows nega la lettura delle connessioni, apri un terminale come amministratore nella cartella e avvia il medesimo file `.bat`.

In alternativa, da PowerShell nella cartella:
>>>>>>> 812fccb (Add public IP display and interactive MEDUSA actions)

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe main.py
```

<<<<<<< HEAD
## ✨ Features

### 🔎 Explore your connections
- Monitor services such as **HTTPS, DNS, SMB, RDP, and SSH**.
- Inspect the **process, PID, local address, remote address, and connection state**.
- Browse the PC’s **TCP and UDP sockets across IPv4 and IPv6**, beyond the five monitored services.
- Filter and search the port inventory by **port, process, PID, or IP address**.

### 📡 Follow network activity
- View real-time **download and upload rates** for your PC.
- Check active TCP connections and newly observed connections on the monitored services during the last **60 seconds**.
- Explore remote endpoints through an **interactive radar**.
- Select a radar endpoint to inspect its associated connection.

### 🛑 Take action
- **Close a supported TCP IPv4 connection** without terminating the entire application.
- **Terminate a selected process**, closing its associated connections.
- Review the target in a confirmation dialog before proceeding.

### 🪼 Keep it close
- Switch to a **compact view** for quick desktop checks.
- Collapse the radar, traffic panel, and individual services.
- Keep MEDUSA **always on top** when needed.
- Enjoy smooth transitions, an animated mascot, and a teal-to-charcoal interface.
- Network collection runs separately from the interface to keep the application responsive.

---

## 💡 Built for quick checks

MEDUSA is designed to be a convenient tool you can keep at hand throughout the day.

Use it to answer everyday questions:

- **Which application is using this connection?**
- **Where is my PC connecting?**
- **Which ports are listening?**
- **How much network traffic is there right now?**
- **Can I close this connection or stop the process behind it?**

Open it, inspect the activity, and take action from the same interface.

---

## ⚙️ What to know

- Closing individual connections currently supports **TCP IPv4 on Windows** and requires administrator privileges. An application may reconnect afterward.
- Terminating a process closes the entire program and may discard unsaved work.
- The port inventory shows sockets visible to MEDUSA through the operating system. A listening port is **not necessarily reachable from the Internet**.
- Traffic rates are measured for the **whole PC**, not per connection.
- The radar is a visual arrangement of observed endpoints, **not a geographic map or an active network scan**.
- Status indicators and animations describe activity or monitoring conditions. They **do not provide security verdicts**.
=======
Per avviare nuovamente da PowerShell nella cartella **MEDUSA-0.4.2**:

```powershell
.\AVVIA_MEDUSA.bat
```
>>>>>>> 812fccb (Add public IP display and interactive MEDUSA actions)

Il terminale mostra versione e percorso completo; in fondo alla barra laterale deve comparire **MEDUSA 0.4.2**. Usa la nuova cartella per evitare di avviare una copia precedente.

## Uso

<<<<<<< HEAD
MEDUSA is actively being developed.

The goal is to build an approachable **network visibility and control tool**: useful for everyday checks, clear enough for learners, and convenient for users who want to understand what their PC is doing on the network.

It is not currently an antivirus, firewall, or intrusion detection system.
=======
- Clic sull'intestazione **RADAR** per comprimerlo. Anche **Traffico PC** e ogni servizio sono richiudibili. La finestra mantiene le dimensioni mentre chiudi una sezione; trascina l'angolo inferiore destro per ridimensionarla.
- Trascina la barra superiore per spostare la finestra. Doppio clic per massimizzare/ripristinare. **PIN** mantiene MEDUSA in primo piano.
- Il radar mostra endpoint remoti **osservati sui cinque servizi**; posizione e distanza sono organizzazione grafica, non geolocalizzazione. Non esegue sonde, ping, scansioni delle porte o blocchi firewall.
- Clic su un punto: si apre il servizio corrispondente e viene selezionata la connessione. Il mouse mostra un suggerimento; con il radar a fuoco, frecce destra/sinistra selezionano gli endpoint.
- Il filtro **Tutti / IPv4 / IPv6** agisce sul radar. Le tabelle restano complete. Per non appesantire l'animazione sono disegnati al massimo 100 endpoint; tutte le righe rimangono consultabili sotto.
- Ogni tabella mostra processo, PID, endpoint remoto e stato. Clic sulla riga per visualizzare anche l'endpoint locale, **Ctrl+C** per copiare i dettagli. **Mostra tutte** espande le righe, con scorrimento per elenchi lunghi.
- Il comando Pausa animazione è stato rimosso. I timer grafici si sospendono automaticamente quando il relativo pannello è nascosto o la finestra è minimizzata. La medusa usa un'immagine con lieve pulsazione e oscillazione complessiva: non è un modello con tentacoli controllabili separatamente. I punti appena osservati pulsano per circa 1,5 secondi.
- I colori delle connessioni non sono giudizi di sicurezza. Nessuno stato sospetto/critico è dedotto dal volume di traffico.
- La geometria, le sezioni aperte e PIN sono salvati con QSettings. Non vengono salvati i log delle connessioni né inviati inventari a servizi esterni. La rilevazione dell’IP pubblico interroga ipify come descritto sotto.

## Cosa misurano i numeri

- **Connessioni attive**, **IPv4/IPv6**: connessioni TCP `ESTABLISHED` di tutto il PC, anche su porte diverse dai cinque servizi. Non devono necessariamente coincidere con la somma delle righe dei servizi.
- **Nuove / 60 s**: connessioni remote osservate sui cinque servizi negli ultimi 60 secondi. Il primo campione include quelle già aperte al lancio. Le socket `LISTEN` sono escluse da questo contatore, ma rimangono nelle tabelle.
- Un collegamento può comparire in più gruppi se porta locale e remota appartengono a servizi monitorati; il radar distingue servizio ed endpoint.
- **IP locale**: primo indirizzo non loopback fra le connessioni TCP stabilite; il suggerimento mostra gli altri. Non è una rilevazione dell'IP pubblico e può essere vuoto senza connessioni.
- **Download/upload**: contatori aggregati delle interfacce del PC letti da psutil; sono totali host, non per sito o processo. Possono includere interfacce virtuali. Le unità KB/s, MB/s sono calcolate su base 1024. Il grafico mostra fino a 60 secondi con scala automatica comune.
- **Aggiornamento 1 s**: intervallo richiesto; una lettura lenta o limitazioni del sistema possono allungarlo. Dopo cinque secondi senza aggiornamento la UI segnala l'attesa. Su errore conserva l'ultimo campione e lo segnala come potenzialmente precedente.
- UDP/DNS: psutil può mostrare solo una socket locale senza destinazione e può non intercettare richieste molto brevi fra due campioni; non è un packet sniffer e non identifica domini HTTPS.
- **Servizi monitorati 5** indica la configurazione, non cinque servizi necessariamente attivi.
>>>>>>> 812fccb (Add public IP display and interactive MEDUSA actions)

Il mockup aveva colonne byte per connessione e loghi di siti: non sono presenti nel programma, perché il backend non fornisce queste misure e il design approvato ha rimosso i loghi. Tutti i dati della UI normale provengono dal PC, non dalle cifre illustrative degli screenshot.

<<<<<<< HEAD
## 🛠️ Built With

**Python** · **PySide6** · **psutil**
=======
## Verifica effettuata

Test automatici Qt offline: espansione/compressione, selezione/copia, IPv6, elenchi lunghi, errori e recupero, cronologia e arresto del worker. Avvio con il collector reale verificato nell'ambiente Linux disponibile. Le anteprime in `preview/` usano dati dimostrativi espliciti.
>>>>>>> 812fccb (Add public IP display and interactive MEDUSA actions)

**Da provare sul PC Windows:** bordi e trascinamento della finestra, PIN, rendering Segoe UI/Consolas, permessi psutil e servizio SMB Windows. Non viene distribuito un EXE: il pacchetto contiene i sorgenti eseguibili con Python.

<<<<<<< HEAD
**Observe. Understand. React.**
=======
Esecuzione test dalla cartella:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```
>>>>>>> 812fccb (Add public IP display and interactive MEDUSA actions)

## Spie dei servizi

Verde: connessioni attive. Giallo: socket in ascolto, senza connessioni remote. Blu spento: inattivo (anche SMB Server fermo). Rosso: errore di lettura, dati non aggiornati; non indica da solo una minaccia. Lo stato è disponibile anche come testo e tooltip. Le porte sono visualizzate in badge separati.

## Radar e movimento

Radar circolare con doppio bordo graduato, anelli concentrici, riferimenti N/E/S/W decorativi, scia sfumata e punti luminosi selezionabili. La posizione è logica: non indica una posizione geografica. La scia non invia pacchetti e non esegue scansioni.

Le animazioni usano timer Qt (radar 16 ms, traffico 33 ms): la frequenza effettiva dipende dal PC. Le tendine si aprono e chiudono in 240 ms, anche invertendo il movimento con clic ripetuti. La finestra mantiene le dimensioni durante l'apertura; puoi ridimensionarla manualmente. I timer grafici si fermano per i pannelli nascosti e la finestra ridotta a icona.

Le immagini in `preview/` mostrano catture dell’app Qt con dati dimostrativi. La medusa mantiene la grafica approvata con lieve oscillazione; i tentacoli non sono animati singolarmente.

## Chiudere una connessione

1. Su Windows, avvia `AVVIA_MEDUSA.bat` con **Esegui come amministratore** (tasto destro). Il monitoraggio può funzionare anche senza elevazione, ma la chiusura richiede privilegi amministrativi.
2. Apri il servizio e seleziona una riga **TCP IPv4 ESTABLISHED**. Puoi raggiungerla anche selezionando un punto sul radar.
3. Premi **Chiudi connessione**. Controlla processo, PID, endpoint locale e remoto nel dialogo; premi **Annulla** oppure conferma la chiusura.
4. MEDUSA ricontrolla l’identità del processo e la presenza della stessa connessione prima di inviare la richiesta a Windows. Se non esiste più, non esegue la chiusura. Il dialogo riporta l’esito restituito dall’API; le tabelle vengono aggiornate dal normale monitoraggio.

La funzione usa `SetTcpEntry` con `MIB_TCP_STATE_DELETE_TCB`. Interrompe la singola sessione senza terminare il processo e senza creare regole firewall. Download, trasferimenti SMB o sessioni SSH/RDP possono interrompersi. Il programma può aprire subito una nuova connessione: non è un blocco permanente.

**Limiti:** solo Windows e TCP IPv4; non UDP, DNS su UDP, IPv6 o socket LISTEN. Il pulsante rimane disabilitato per righe non supportate o identità non verificabile; il tooltip spiega il motivo. Il processo viene identificato con PID e istante di creazione, la connessione con i due indirizzi e le due porte. Windows accetta solo gli endpoint nell’operazione finale: resta un brevissimo intervallo fra verifica e richiesta durante il quale lo stato può cambiare.

**Verifica:** test automatici della struttura nativa, indirizzi/porte, controllo identità, connessione scomparsa, accesso negato simulato; prove Qt di selezione stabile e annullamento. La chiusura effettiva su Windows **non è stata eseguita in questo ambiente Linux**: va provata su una connessione non importante prima dell’uso abituale.

Documentazione API: https://learn.microsoft.com/en-us/windows/win32/api/iphlpapi/nf-iphlpapi-settcpentry

## Diventa widget

**Diventa widget** trasforma MEDUSA in un pannello di 320 px, posizionato inizialmente in basso a destra nell’area disponibile dello schermo, sopra la barra delle applicazioni. Trascina l’intestazione MEDUSA per spostarlo. **Apri ↗** ripristina la finestra completa e le sue sezioni; se lo chiudi in modalità widget, il prossimo avvio usa la geometria della finestra completa.

Il widget mostra soltanto i servizi monitorati attivi (HTTPS, DNS, SMB, RDP e SSH), con porta e numero di connessioni. Non sostituisce l’inventario generale **Tutte le porte**. Se nessun servizio è attivo compare un messaggio dedicato. Errori o aggiornamenti in ritardo vengono segnalati, senza presentare le vecchie misure come live. Il monitoraggio continua, mentre i timer del radar e del grafico nascosti sono sospesi.

La nuova tonalità laguna sfuma da #155c60 al grigio ardesia #171c25. Download e upload nella barra superiore hanno etichette e valori distinti. Medusa, radar, spie e badge sono conservati.

## Tutte le porte del PC

Premi **Tutte le porte** nella barra laterale. Questa vista non è limitata a 443, 53, 445, 3389 e 22: legge tutte le socket TCP/UDP IPv4/IPv6 restituite dal sistema operativo.

- **In ascolto / UDP** (predefinito): TCP LISTEN e socket UDP associate a una porta locale. UDP non ha uno stato LISTEN equivalente a TCP: viene mostrato come «Associata».
- **Tutte le socket**: include anche porte locali delle connessioni stabilite e gli altri stati TCP.
- **Solo TCP / Solo UDP**, filtro IPv4/IPv6 e ricerca per porta, processo, PID o indirizzo. I filtri possono essere combinati.
- Colonne: porta locale, protocollo/famiglia, indirizzo locale, processo, PID, stato, ambito del bind. La selezione mostra l’endpoint remoto completo.
- **Solo PC**: bind loopback. **Tutte le interfacce**: bind wildcard 0.0.0.0 oppure :: nella rispettiva famiglia. **Interfaccia locale**: indirizzo specifico. Queste etichette non misurano l’esposizione a Internet né il comportamento dual-stack.
- Nessun limite di cinque servizi e nessun limite di 100 righe nella tabella: gli elenchi scorrono. I conteggi indicano socket, non numeri di porta univoci; più processi/famiglie possono usare la stessa porta.

Per la visibilità più completa, avvia come amministratore. «Tutte» significa tutte le socket che il sistema rende visibili al processo nel campione corrente; processi protetti e socket molto brevi possono limitare l’osservazione. Non si esegue una scansione esterna: firewall, router e NAT determinano la raggiungibilità da fuori. Il radar e la cronologia recenti restano dedicati ai cinque servizi; l’inventario generale è separato.

## Terminare un processo

Seleziona una riga nei servizi o in **Tutte le porte**, poi **Termina processo**. Il dialogo mostra nome e PID e permette di annullare; la scelta predefinita è Annulla.

MEDUSA controlla PID e istante di creazione prima di intervenire, per evitare di colpire un altro processo dopo il riutilizzo del PID. L’operazione avviene in un thread separato. Su Windows `psutil.Process.terminate()` termina immediatamente il processo: tutte le sue connessioni si chiudono e i dati non salvati possono andare persi. Non termina automaticamente l’albero dei processi; un servizio potrebbe riavviarsi da solo.

PID 0–4 e MEDUSA sono esclusi. Non è una lista esaustiva dei processi critici: evita di terminare processi di sistema che non conosci. I processi protetti o di altri utenti possono restituire accesso negato. La funzione non tenta di aggirare tali protezioni. Se il processo rimane attivo dopo tre secondi, viene riportato il timeout senza ulteriori tentativi.

**Differenza:** Chiudi connessione interrompe una singola sessione TCP IPv4; Termina processo interrompe il programma intero. Per UDP e IPv6 la seconda azione può essere disponibile anche quando la prima non lo è.

## Verifica dell’aggiornamento

17 test automatici passati: inventario IPv4/IPv6 e porte fuori dai cinque servizi, TCP/UDP e bind, rifiuto PID esclusi, PID riutilizzato, accesso negato, terminazione reale di un processo figlio di test su Linux; restano i test precedenti di monitoraggio, chiusura connessione e animazioni. Prove Qt aggiuntive di ricerca, filtro famiglia, selezione e annullamento. Il comportamento nativo Windows e il rendering DPI vanno ancora collaudati sul PC di destinazione.

## IP pubblico

La barra laterale mostra l’IP pubblico IPv4 o IPv6 osservato dal servizio HTTPS ipify (https://api64.ipify.org?format=json). Rilevamento all’avvio e ogni 60 secondi, oppure con **Aggiorna IP** dopo un cambio rete/VPN. La richiesta è asincrona, con timeout di trasferimento di 6 secondi; non interrompe il monitoraggio. Se fallisce compare **Non disponibile** anziché un vecchio IP presentato come attuale.

Il servizio riceve la richiesta e ne vede l’IP di origine; MEDUSA non invia processi, inventario porte o cronologia. Il risultato rappresenta il percorso della richiesta a ipify: split tunneling, proxy e routing per applicazione possono produrre IP diversi per altre connessioni. Non certifica la copertura della VPN e non elenca contemporaneamente tutti gli IP pubblici. Il widget minimale continua a mostrare soltanto i servizi attivi.

## Medusa centrale interattiva

Passando sulla medusa al centro del radar compaiono IP pubblico e locale e il bordo si illumina. Clicca, oppure premi Invio/Spazio con il radar a fuoco, per aprire le azioni **Copia IP pubblico**, **Aggiorna IP pubblico** e **Diventa widget**. Copia è disabilitato quando l’IP non è disponibile.

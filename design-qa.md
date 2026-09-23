# MEDUSA 0.4.0 — verifica

Tema laguna #155c60 → ardesia #171c25, accento menta. Tipografia dei valori di traffico ingrandita, etichette separate, contenitore discreto. Screenshot Qt esaminati: panoramica 1060×850, widget 320×253 con tre servizi dimostrativi, finestra stretta 740×650. Nessun dato dimostrativo nel collector reale.

Widget dedicato: soli servizi monitorati attivi, stato vuoto, avviso di errore o dati scaduti, posizione iniziale in basso a destra, intestazione trascinabile, pulsante di ritorno. Radar e grafico sospesi quando nascosti. Ripristino della geometria e conservazione delle sezioni della finestra completa.

17 test automatici, incluso ingresso/uscita widget, aggiornamenti e gestione errori. Rendering Linux Qt offscreen; trascinamento nativo, font, DPI e posizionamento rispetto alla taskbar da verificare su Windows. Il widget è nativo MEDUSA, non usa le API dei widget Apple.

0.4.1: IP pubblico asincrono via ipify, aggiornamento 60 s e manuale; risposta validata IPv4/IPv6, errori senza valore obsoleto. 19 test offline superati. Sidebar resa più compatta per il nuovo campo. Richiesta live al provider non verificata in questo ambiente.

0.4.2: medusa interattiva, tooltip degli IP, menu di copia/aggiornamento/widget e scorciatoia Invio/Spazio. 20 test offline passati, inclusa copia e disabilitazione in errore. Anteprime aggiornate; validazione live del provider e resa nativa Windows pendenti.

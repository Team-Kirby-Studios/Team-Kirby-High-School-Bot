# Team-Kirby-High-School-Bot

Il bot helper della Team Kirby High School!

## Funzionalità:
- Estrazione casuale fra due estremi di numeri
- Sorteggio fra gli studenti
- Palla avvelenata
- Calcio
- Sistema di abilità sportive
- Gestione degli studenti sorteggiati per i prof
- Divisione degli studenti sorteggiati per materia
- Inserimento voti degli studenti
- Lettura voti per gli studenti, genitori e prof
- Creazione e inserimento voti nelle pagelle
- Visualizzazione delle pagelle per studenti e genitori
- Sistema di voice calls con sistema di riconoscimento di [Tupperbox™](https://tupperbox.app/)

## Palla Avvelenata:
Il gioco di palla avvelanata è molto semplice e intuitivo: /tiropa per tirare contro una persona. L'esito dipende dalla skill 'tiropa' del tiratore e del difendente.
Possibilità di colpire, mancare e schivare in base alle skill.

## Calcio:
Vari comandi per giocare. /passaggio, /dribbling, /contrasto, /tiro, /fallo, /crossbar_challenge.
- /passaggio: Si passa la palla ad un compagno, più è alta la skill 'passaggio', più probabilità si hanno di passare correttamente. Se il passaggio viene intercettato, i giocatori sono liberi di scegliere chi intercetta, in base al contesto della situazione.
(Esempio: Se il gioco è a centrocampo, un centrocampista avversario dovrebbe essere la persona che intercetta.)

- /dribbling: Si tagga una persona da dribblare. Gli esiti sono: Avversario superato, Fallo subito, Avversario non superato e Fallo commesso. Gli esiti dipendono dalla skill 'dribbling' di chi fa il comando, e dalla skill 'contrasto' del difendente. I primi due esiti sono positivi per l'attaccante, gli altri due positivi per il difendente.
  - Avversario superato: Il dribbling è riuscito.
  - Fallo subito: Il difendente ha commesso fallo su di te.
  - Dribbling non riuscito: Il dribbling non è riuscito e il difendente ha recuperato palla.
  - Fallo commesso: Nel tentativo di superare l'avversario, hai commesso tu fallo contro di lui/lei.

- /contrasto: È l'inverso del /dribbling. Chi fa il comando usa la skill 'contrasto', chi viene contrastato usa sia la skill 'dribbling' che la skill 'contrasto'.
  - Contrasto riuscito: Autoesplicativo. Hai recuperato palla sull'avversario.
  - Contrasto non riuscito: Anche questo autoesplicativo. Hai fallito il contrasto e l'attaccante può avanzare.
  - Fallo subito: Mentre contrastavi l'avversario, il tuo avversario ha fatto fallo su di te nel cercare di proteggersi.
  - Fallo commesso: Sei stato troppo vigoros* nell'intervento e hai commesso fallo. È la vita del difensore questa, capita.

- /tiro: Per calciare in porta. Qui sono prese in causa la skill 'tiro' del tiratore, e 'portiere' di chi sta in porta.
  - Gol: Hai tirato e segnato. GG.
  - Parata: Il portiere ha parato il tiro;
    - Bloccata: Il portiere ha anche bloccato la palla e ora è sua.
    - Respinta corta: Il portiere ha parato, ma la palla è ancora lì vicino. Sta ai giocatori decidere se arriva prima un difensore o un attaccante.
    - Palla fuori: Dopo la parata del portiere, la palla va lontana, in rimessa laterale o calcio d'angolo. È un 50/50.
  - Tiro fuori: Hai mancato la mira e la palla è andata fuori.
  - Palo: Hai angolato un po' troppo e hai colpito uno dei due pali. F.
  - Traversa: Hai alzato un po' troppo la mira, hai colpito la traversa. Non è una crossbar challenge questa xD.

- /fallo: Di base è per i prof di motoria, ma si può impostare a chi fa da arbitro. Serve per decidere in modo casuale l'esito di un fallo.
  - No cartellino: Solo fallo fischiato. Nessun cartellino.
  - Cartellino giallo: Chi ha commesso il fallo si prende un'ammonizione. Alla prossima è espulso.
  - Cartellino rosso: Chi ha commesso fallo, ha fatto un brutto fallo. Espulso.

- /crossbar_challenge: Permette di giocare la crossbar_challenge, un classico dei tempi d'oro di Youtube Italia (bei tempi le crossbar challenge dei Mates).
  - Traversa: Hai colpito la traversa. GGEZ.
  - Gol: La porta è vuota, giustamente è facile segnare. Ma qui non è l'obiettivo.
  - Palo: Hai colpito il palo. Capita.
  - Tiro fuori: Hai calciato male, palla fuori.

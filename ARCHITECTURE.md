ARCHITECTURE
Progetto: 2x3
Versione: Build 0.1
Scopo del progetto
2x3 è un'applicazione Open Source che permette di trasformare:
Video → Modello 3D
Immagini → Modello 3D
utilizzando esclusivamente software Open Source.
L'obiettivo è costruire una piattaforma modulare, facilmente estendibile e adatta a crescere nel tempo senza richiedere modifiche strutturali.
Principi dell'architettura
L'architettura del progetto segue questi principi fondamentali:
Open Source come requisito obbligatorio.
Sviluppo Cloud First.
Repository GitHub come fonte ufficiale del progetto.
Struttura delle cartelle stabile.
Componenti indipendenti tra loro.
Facilità di manutenzione.
Facilità di espansione.
Compatibilità con hardware più potente in futuro.
Ambiente di sviluppo
Lo sviluppo ufficiale viene eseguito tramite GitHub Codespaces.
I computer dell'utente vengono utilizzati esclusivamente per accedere al Codespace tramite browser.
L'architettura non deve dipendere dalle caratteristiche hardware del computer utilizzato.
Struttura del progetto
assets/
config/
data/
logs/

src/
    core/
    gui/
    pipeline/
    utils/

tests/
Questa struttura rappresenta l'organizzazione ufficiale del progetto e non deve essere modificata senza una decisione documentata.
Ruolo delle cartelle
assets/
Contiene le risorse del progetto.
Esempi:
immagini
icone
materiali di esempio
config/
Contiene tutti i file di configurazione.
Le impostazioni devono essere centralizzate per evitare modifiche al codice.
data/
Contiene i dati utilizzati durante l'elaborazione.
Ad esempio:
immagini importate
video importati
risultati intermedi
modelli generati
logs/
Contiene i registri delle operazioni eseguite dall'applicazione.
src/
Contiene tutto il codice sorgente.
È suddiviso in moduli specializzati.
core/
Funzioni fondamentali del progetto.
Esempi:
configurazione
gestione dei log
funzioni comuni
gui/
Interfaccia grafica dell'applicazione.
La GUI dovrà essere separata dalla logica interna.
pipeline/
Gestisce il flusso di elaborazione.
Il suo compito sarà coordinare le varie fasi di conversione.
utils/
Funzioni di supporto riutilizzabili.
tests/
Contiene tutti i test del progetto.
Ogni nuova funzionalità dovrà essere accompagnata dai relativi test.
Flusso di elaborazione
Il flusso previsto sarà il seguente:
Importazione del file.
Controllo del formato.
Preparazione dei dati.
Elaborazione.
Generazione del modello 3D.
Esportazione del risultato.
Registrazione delle operazioni nel log.
Modularità
Ogni componente deve poter essere modificato o sostituito senza richiedere cambiamenti all'intero progetto.
Questo permetterà di introdurre in futuro nuovi algoritmi e nuove tecnologie mantenendo stabile l'architettura.
Scalabilità
L'architettura è progettata per funzionare sia su hardware limitato sia su macchine molto più potenti.
L'aumento delle prestazioni dovrà richiedere esclusivamente un aggiornamento dell'ambiente di esecuzione, senza modificare la struttura del software.
Documentazione
Ogni Build dovrà mantenere aggiornati almeno i seguenti documenti:
README.md
PROJECT_STATE.md
CHANGELOG.md
DECISIONS.md
Conclusione
Questa architettura rappresenta il riferimento ufficiale della Build 0.1.
Ogni evoluzione futura del progetto dovrà rispettare i principi definiti in questo documento oppure introdurre modifiche esplicitamente documentate.
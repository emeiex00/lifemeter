# LifeMeter con Supporto MIDI

## Novità

LifeMeter ora supporta l'invio di accordi MIDI a dispositivi virtuali, sostituendo il semplice beep sonoro con accordi musicali che variano in base alla percentuale di verde rilevata nell'immagine.

## Come funziona

1. **Installazione di pygame**: Per utilizzare la funzionalità MIDI, è necessario installare la libreria pygame:
   ```
   pip install pygame
   ```

2. **Configurazione di loopMIDI**: Come descritto nel file ISTRUZIONI_MIDI.md, è necessario installare e configurare loopMIDI per creare porte MIDI virtuali.

3. **Utilizzo in LifeMeter**:
   - Avvia LifeMeter
   - Nella sezione "Configurazione MIDI", clicca su "Aggiorna" per visualizzare i dispositivi MIDI disponibili
   - Seleziona la porta MIDI virtuale creata con loopMIDI
   - Seleziona l'opzione "MIDI" invece di "Beep" nella sezione audio
   - Carica un'immagine per analizzare la percentuale di verde

## Dettagli tecnici

- Quando viene rilevato il verde nell'immagine, LifeMeter invia un accordo maggiore tramite MIDI
- L'altezza dell'accordo è proporzionale alla percentuale di verde rilevata
- Più verde = accordo più acuto
- L'accordo è composto da tre note: fondamentale, terza maggiore e quinta

## Risoluzione dei problemi

- Se non vedi dispositivi MIDI, assicurati che loopMIDI sia in esecuzione e che sia stata creata una porta MIDI virtuale
- Se ricevi un errore durante l'inizializzazione MIDI, verifica che pygame sia installato correttamente
- Se l'audio MIDI non funziona, prova a selezionare un dispositivo diverso o a riavviare l'applicazione

## Compatibilità

Questa funzionalità è stata testata su Windows e richiede:
- Python 3.x
- pygame
- loopMIDI (per Windows)
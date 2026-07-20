# Eventi Certe Notti — feed Markdown auto-aggiornato

Questo repository genera e mantiene aggiornato il file **[eventi.md](eventi.md)**,
l'elenco dei prossimi eventi pubblicati su https://www.certenotti.eu/eventi/

## Link pubblico al file (sempre aggiornato)

```
https://raw.githubusercontent.com/IvanLaoMarketing/certenotti-eventi/main/eventi.md
```

## Come funziona

1. Un GitHub Action gira ogni 6 ore (o manualmente dalla tab *Actions* → *Run workflow*).
2. Lo script `scripts/aggiorna_eventi.py` legge la pagina pubblica `/eventi/` del sito
   (titolo, data, ora, link di ogni evento) e arricchisce ogni evento con la
   descrizione completa presa dalla REST API pubblica di WordPress.
3. Se ci sono novità, `eventi.md` viene aggiornato con un commit automatico.

Nessuna credenziale WordPress necessaria: vengono usate solo pagine pubbliche del sito.

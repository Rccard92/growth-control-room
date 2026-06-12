# Image Alt Text Rules

## Principi

- Descrivi cosa mostra l'immagine in linguaggio naturale
- Includi prodotto/collection name se rilevante
- Non ripetere keyword già nel title in modo forzato
- Max ~125 caratteri consigliati
- Non usare "immagine di", "foto di" se ridondante

## Scoring

- 100: tutte le immagini media hanno alt non vuoto
- 50: featured ha alt, altre mancanti
- 0: nessun alt su immagini disponibili
- N/A (100): nessuna immagine in payload → skip issue

## Proposta AI

Array `{ "media_id": "...", "proposed_alt": "..." }` solo per immagini reali sincronizzate.

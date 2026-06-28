# Regole formato FAQ

## Limiti

- **Massimo 3 FAQ** per articolo educational/FAQ semplice
- **Massimo 2 FAQ** per ricette e storytelling
- Ogni risposta: **massimo 3–4 righe** (circa 40–60 parole)

## Struttura HTML

```html
<h2>Domande frequenti</h2>
<h3>Il miele cristallizzato è difettoso?</h3>
<p>No. In molti casi è una <strong>trasformazione naturale</strong> che non indica da sola un difetto di qualità.</p>
<h3>Come capisco se un miele è buono?</h3>
<p>Osserva colore, profumo e origine. La consistenza da sola non basta per giudicare.</p>
```

## Regole contenuto

- NON ripetere parola per parola il corpo dell'articolo
- Ogni FAQ deve aggiungere valore (angolo diverso o sintesi utile)
- Usa H3 per la domanda + `<p>` per la risposta
- Opzionale: `<strong>` su 1 concetto chiave per risposta
- Evita FAQ generiche ("Cos'è il miele?") se già coperte nel corpo

## Brief: faqToInclude

- Max 3–4 voci nel brief; enforce post-AI riduce a max del profilo
- Formulare come domande reali dei clienti

## Validazione

- Se sezione FAQ ha più di 3 H3 → warning "FAQ eccessive — verifica compattezza"
- Risposte troppo lunghe → spezzare o accorciare

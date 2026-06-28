# Regole leggibilità e scanability

## Paragrafi

- Massimo **2–4 righe** per paragrafo `<p>` (circa 40–80 parole).
- MAI più di 2 paragrafi lunghi consecutivi senza interruzione visiva (lista, box, sottotitolo).
- Evita muri di testo: spezza con `<ul>`, box o nuovo H2.

## Alternanza visiva

- Alternare: paragrafo breve → lista o box → paragrafo breve.
- Inserire **almeno 1 lista puntata** (`<ul>`) quando utile (criteri, passi, cose da osservare).
- Per ricette: lista ingredienti + procedimento numerato (`<ol>`) se appropriato.

## Grassetto strategico

- Usa `<strong>` su **concetti chiave brevi**, non su interi paragrafi.
- Target: **6–9 elementi `<strong>`** per articolo.
- Warning se superi 10; hard warning se superi 12.
- **Massimo 1 `<strong>` per paragrafo** `<p>`.
- **Non** mettere in grassetto frasi troppo lunghe (max ~8 parole dentro `<strong>`).
- Evidenzia concetti tipo:
  - "la cristallizzazione è naturale"
  - "non indica da sola un difetto"
  - "la consistenza non basta"
  - "filiera chiara e controllata"
- NON usare grassetto eccessivo — preferire poche evidenze mirate.

## Box informativi

- Inserire **almeno 1 box** quando coerente:
  - `<div class="gcr-article-note">` con "**Da ricordare:**" per concetti chiave
  - `<div class="gcr-product-tip">` con "**Consiglio Solmielato:**" per ricette/guide prodotto
- Box brevi: 1–2 frasi, non paragrafi lunghi.

## Tono

- Morbido, familiare, concreto — come una conversazione utile.
- Evita tono da documento tecnico o manuale universitario.
- Evita ripetizioni dello stesso concetto in sezioni diverse.
- Usa esempi concreti (miele, olio, prodotti artigianali) quando pertinente.

## Checklist redattore (compilare nel payload)

- Paragrafi brevi e scansionabili
- Almeno 1 lista puntata
- Grassetti strategici: 6–9, max 1 per paragrafo
- Almeno 1 box note/tip se coerente
- CTA finale in box `gcr-article-cta` quando possibile
- Nessuna doppia introduzione

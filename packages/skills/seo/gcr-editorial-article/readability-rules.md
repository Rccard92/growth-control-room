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

- Usa `<strong>` su **frasi chiave**, non su interi paragrafi.
- Target: **5–10 elementi strong** per articolo (minimo 4, massimo 12).
- Evidenzia concetti tipo:
  - "la cristallizzazione è naturale"
  - "non indica da sola un difetto"
  - "la consistenza non basta per giudicare la qualità"
- NON usare grassetto eccessivo — max 1–2 strong per sezione H2.

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
- Grassetti strategici (non eccessivi)
- Almeno 1 box note/tip se coerente
- CTA finale presente
- Nessuna doppia introduzione

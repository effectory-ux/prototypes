# Gedeelde namen: de Worker uitrollen

Eenmalig, daarna hoef je hier nooit meer te komen. Zonder deze Worker werkt de
galerij gewoon, alleen blijven hernoemde namen dan in je eigen browser staan.

## 1. Cloudflare-account

Maak een gratis account op [dash.cloudflare.com/sign-up](https://dash.cloudflare.com/sign-up)
als je er nog geen hebt. Je hoeft geen domein te koppelen en geen betaalgegevens
op te geven.

## 2. Inloggen

```bash
npx wrangler login
```

Dit opent je browser. Klik op **Allow**.

## 3. Opslag aanmaken

```bash
cd worker && npx wrangler kv namespace create NAMES
```

Je krijgt een `id` terug. Zet die in `wrangler.toml` op de plek van
`VUL_HIER_DE_KV_ID_IN`.

## 4. Een sleutel kiezen en uitrollen

De sleutel is wat collega's één keer invullen voordat ze mogen hernoemen. Kies
iets dat je makkelijk deelt in Teams, het hoeft geen wachtwoord te zijn.

```bash
npx wrangler secret put EDIT_KEY
```

```bash
npx wrangler deploy
```

Je krijgt een URL terug, zoiets als
`https://prototype-names.<jouw-subdomein>.workers.dev`.

## 5. De galerij erop aansluiten

Zet die URL in `prototypes.json`:

```json
"sync": { "url": "https://prototype-names.<jouw-subdomein>.workers.dev" }
```

Daarna `./build-gallery.py` draaien en committen. Vanaf dat moment is hernoemen
in de galerij meteen zichtbaar voor iedereen.

## Werkt het?

```bash
curl https://prototype-names.<jouw-subdomein>.workers.dev/names
```

Hoort `{}` terug te geven, of de namen die er al staan.

## Kosten

De gratis laag van Cloudflare Workers is 100.000 verzoeken per dag. Een
galerij die een paar keer per dag geopend wordt zit daar niet in de buurt.

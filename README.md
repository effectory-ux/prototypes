# Prototypes · Effectory UX

Centrale ingang voor alle prototypes van het UX-team, over meerdere repos en
accounts heen. Eén kaart per prototype, met een live thumbnail. De knop op de
kaart opent een modal met alle pagina's van dat prototype en de repo waar het staat.

**Live:** https://effectory-ux.github.io/prototypes/

---

## De werkwijze in drie regels

1. **Je werkt nooit op `main`.** Eigen branch, pull request, mergen.
   GitHub weigert een directe push, dus dit kun je niet vergeten.
2. **Één prototype is één bestand** in `data/prototypes/`. Jij raakt jouw
   bestand aan, niemand anders. Daarom kunnen twee mensen niet botsen.
3. **De pagina bouwt zichzelf.** `index.html` staat niet meer in de repo.
   GitHub bouwt en publiceert hem na elke merge, en elke werkdagochtend opnieuw.

Merge je eigen pull request zodra de check groen is. Wachten op een collega
hoeft niet.

## Eenmalig instellen

```bash
git clone https://github.com/effectory-ux/prototypes.git && cd prototypes && ./setup.sh
```

Dat zet een waarschuwing aan voor als je per ongeluk op `main` commit, zodat je
dat merkt voordat je werk erop staat.

## Een naam wijzigen vanaf de pagina

Klik op het potloodje naast een kaartnaam en typ een nieuwe. Je ziet het meteen,
maar alleen bij jezelf: de wijziging staat in je eigen browser (`localStorage`).
GitHub Pages serveert alleen statische bestanden, dus er is geen server die het
voor iedereen kan bewaren.

Onderin verschijnt een balk met **Publiceren**. Die zet het bestand van dát ene
prototype op je klembord en opent de GitHub-editor erop: alles selecteren,
plakken, **Commit changes**. Omdat `main` op slot zit maakt GitHub er zelf een
pull request van. Mergen, en binnen een minuut ziet iedereen de nieuwe naam.

Er gaat dus één klein bestand over de lijn, niet de hele lijst. Publiceer je een
naam terwijl deze pagina al een uur openstaat, dan kun je daarmee nooit een
prototype weggooien dat er inmiddels bij is gekomen.

**Ongedaan maken** wist je lokale wijzigingen en zet de namen terug op wat er
gepubliceerd is.

### Zonder publiceerstap

Zet je in `data/site.json` een URL bij `sync.url`, dan slaat de galerij een naam
direct op voor iedereen en verdwijnt de publiceerstap. `worker/` bevat het
endpoint daarvoor plus uitrolstappen; het is één `GET` en één `PUT`, dus het kan
net zo goed ergens anders draaien dan op Cloudflare. Zolang `sync.url` leeg is,
merkt de pagina er niets van en blijft alles zoals hierboven.

Namen en structuur zijn dan twee verschillende dingen, en dat is met opzet. Een
naam is iets kleins dat je even bijwerkt, dus die mag rechtstreeks. Wélke
prototypes er zijn, waar ze staan en in welke groep ze horen, blijft in git: daar
wil je een historie van, en de mogelijkheid om iets terug te draaien.

## Een prototype toevoegen

```bash
./nieuw-prototype.py
```

Het script stelt een paar vragen, maakt een branch, schrijft één nieuw bestand,
controleert het en opent de pull request. Merge hem als de check groen is.

Liever met de hand? Maak een branch en zet een bestand in `data/prototypes/`.
De bestandsnaam is vrij, houd hem kort en met streepjes:

```json
{
  "name": "Mijn prototype",
  "desc": "Eén regel over wat het laat zien.",
  "owner": "Jente",
  "group": "Platform",
  "repo": "engage",
  "path": "prototypes/mijn-prototype.html",
  "also": ["^prototypes/mijn-prototype-"]
}
```

- `path` is de pagina die de kaart opent. Zet hier de nieuwste versie, want dat
  is wat iemand ziet als hij op de thumbnail klikt.
- `also` claimt de overige schermen van hetzelfde prototype, zodat het één kaart
  blijft in plaats van vijf losse.
- `group` moet in de lijst in `data/site.json` staan. Die lijst bepaalt ook de
  volgorde van de secties op de pagina. Een nieuwe groep voeg je daar toe.
- `repo` is de sleutel van een bestand in `data/repos/`.

Heeft één prototype meerdere ingangen, bijvoorbeeld dezelfde flow met andere
data of een andere ontwerprichting, dan zet je die als `variants`. De kaart
opent altijd de eerste, en een knopje "N pagina's" opent een modal met de
hele lijst:

```json
"variants": [
  { "label": "Novanta · Q2", "path": "novanta-before-overview.html" },
  { "label": "Novanta · Q3", "path": "novanta-after-overview.html" }
]
```

Laat je `variants` weg terwijl een prototype meer pagina's heeft, dan verzint de
generator de labels uit de bestandsnamen: het deel dat alle namen delen gaat
eraf, dus `group-linking-bol.html` wordt "Bol".

Controleer je werk voor je pusht:

```bash
./build-gallery.py --check --base origin/main
```

Dat is precies wat GitHub op je pull request draait. Hij noemt het bestand én wat
eraan mankeert, en meldt alle problemen in één keer.

De check onderscheidt twee dingen. Iets fout in het bestand zelf — een ontbrekend
veld, een typo in een groepsnaam, kapotte JSON — blokkeert altijd. Een pagina die
niet bestaat blokkeert alleen als jij de verwijzing toevoegt. Stond hij er al en
heeft iemand het bestand in zijn eigen repo verplaatst, dan krijg je een melding
maar geen rood kruis. Je wijziging hoort niet stil te staan door het opruimwerk
van een ander.

## Een nieuwe pagina in een prototype dat er al staat

Niets doen. Push je pagina in je eigen repo en zorg dat de naam onder het
`also`-patroon van je kaart valt. De galerij pikt hem de volgende ochtend op,
of meteen als je in de Actions-tab **Bouwen en publiceren** handmatig start.

## Een prototype aanpassen of weghalen

Pas het bestand in `data/prototypes/` aan, of verwijder het. Zelfde route:
branch, pull request, mergen. Raak je een prototype van iemand anders aan,
overleg dan even — `owner` in het bestand zegt van wie het is.

## Een repo toevoegen

Zet een bestand in `data/repos/`, met de Pages-URL als die er is. De
bestandsnaam is de sleutel die je in `repo` gebruikt:

```json
{
  "repo": "effectory-ux/mijn-repo",
  "pages": "https://effectory-ux.github.io/mijn-repo/",
  "repos": [{ "org": "effectory-ux", "name": "mijn-repo" }],
  "ignore": ["^404\\.html$"]
}
```

Zonder Pages krijgt de kaart geen thumbnail maar een link naar de code.
Gebruik `liveRewrite` als de repo een submap als site-root publiceert, zoals
`cyos` doet met `site/`. De repo moet publiek zijn, anders kan de bouwrobot er
niet in kijken.

## Wat GitHub voor je doet

| Wanneer | Wat |
|---|---|
| Bij elke pull request | `build-gallery.py` controleert de data en rendert de pagina als proef. Rood betekent: nog niet mergen. |
| Na elke merge op `main` | de galerij wordt gebouwd en gepubliceerd, ongeveer een minuut later staat hij live |
| Elke werkdag 07:00 | dezelfde bouw, zodat nieuwe pagina's in de bronrepos automatisch verschijnen |

Het bouwen zelf blokkeert nooit op een pagina die niet bestaat. De kaart blijft
staan, zonder thumbnail, en de melding komt in het log. Een prototype dat stil uit
de galerij verdwijnt omdat iemand een bestand verplaatste is erger dan een kaart
die laat zien dat er iets te repareren valt.

Twee merges kort na elkaar halen elkaar niet in: de tweede bouw wacht op de
eerste in plaats van hem af te breken.

## Waarom je elkaar niet meer kunt overschrijven

Drie dingen die vroeger misgingen, en waarom ze nu niet meer kunnen:

- **Het gegenereerde bestand.** `index.html` is 54 kB machinewerk. Zolang die in
  git stond, herschreef iedereen die bouwde het hele bestand, en botsten twee
  mensen gegarandeerd in code die niemand met de hand kan samenvoegen. Nu bouwt
  GitHub hem en staat hij in `.gitignore`.
- **Één lijst voor iedereen.** Alle 23 prototypes stonden in één array in
  `prototypes.json`, en iedereen zette zijn entry onderaan: dezelfde regels,
  dus dezelfde botsing. Nu is elk prototype een eigen bestand. Verschillende
  bestanden botsen niet, hoe vaak je ook tegelijk toevoegt.
- **Direct op `main` pushen.** Dat overschreef stilletjes het werk van iemand
  die net had gepusht. `main` is nu dicht: alleen via een pull request, en
  force-pushen kan niet meer.
- **Publiceren van een naamswijziging.** Dat plakte de hele `prototypes.json`
  over het bestand heen, uit een pagina die je misschien al een uur openhad.
  Alles wat er in de tussentijd bij kwam, verdween daarmee. Nu gaat er precies
  één prototypebestand over de lijn, met alleen de naam gewijzigd.

Wat nog wél kan botsen: twee mensen die hetzelfde prototypebestand aanpassen.
Dat is precies het geval waarin je even wilt overleggen, en het gaat om tien
regels JSON in plaats van een pagina vol gegenereerde HTML.

## Als het toch misgaat

**Mijn pull request is rood.** Lees de melding onder de check: hij noemt het
bestand en wat eraan mankeert. Meestal wijst `path` naar een pagina die nog
niet gepusht staat in de bronrepo, of staat `group` niet in `data/site.json`.

**Git zegt dat ik niet kan pushen naar main.** Dat hoort zo. Zet je werk op een
branch, je wijzigingen verhuizen mee:

```bash
git switch -c mijn-wijziging && git push -u origin mijn-wijziging
```

**Mijn branch loopt achter.** Haal main op en ga verder; omdat jullie in
verschillende bestanden werken, gaat dit vrijwel altijd zonder gedoe:

```bash
git fetch origin main && git rebase origin/main
```

**De live pagina is stuk.** Ga naar de Actions-tab, zoek de laatste groene
**Bouwen en publiceren** en start hem opnieuw. De bouw is los van de historie,
dus dat zet de vorige versie terug. De inhoud van de kaarten komt live uit de
bronrepos, dus een prototype dat daar stuk staat, repareer je daar.

## Waar staat wat

| Repo | Inhoud |
|---|---|
| [effectory-ux/Engage-Design-system-](https://github.com/effectory-ux/Engage-Design-system-) | het design system: componenten, tokens, iconen, skill |
| [effectory-design/effectory-design-documentation](https://github.com/effectory-design/effectory-design-documentation) | de prototypes van Jente |
| [eray-effectory/action-center](https://github.com/eray-effectory/action-center) | Action Center van Eray, nog zonder Pages |
| [eray-effectory/ux](https://github.com/eray-effectory/ux) | platform design van Eray |
| [effectory-ux/cyos](https://github.com/effectory-ux/cyos) | CYOS survey creation, fase 1 en 2 |
| [N33G3K/cyos-survey-creation-flow-demo](https://github.com/N33G3K/cyos-survey-creation-flow-demo) | losse CYOS-demo van Jamal |

## In deze repo

| Bestand | Wat het is |
|---|---|
| `data/prototypes/*.json` | één bestand per prototype · dit is wat je aanpast |
| `data/repos/*.json` | de bronrepos die uitgelezen worden |
| `data/site.json` | de groepen en hun volgorde, plus de links naar het design system |
| `build-gallery.py` | de generator · `--check` controleert zonder te bouwen |
| `nieuw-prototype.py` | vraagt-en-doet: branch, bestand, controle, pull request |
| `template.html` | de pagina zelf: opmaak en gedrag van de kaarten |
| `tokens.css`, `foundation.css` | kopieën uit het design system, zodat deze pagina dezelfde kleuren en spacing gebruikt |

Thumbnails zijn geen plaatjes maar de echte pagina in een verkleinde iframe, pas
geladen als de kaart in beeld komt. Ze zijn dus altijd actueel.

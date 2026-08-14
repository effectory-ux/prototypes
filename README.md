# Prototypes · Effectory UX

Centrale ingang voor alle prototypes van het UX-team, over meerdere repos en accounts heen.
Eén kaart per prototype, met een live thumbnail. De knop op de kaart opent een
modal met alle pagina's van dat prototype en de repo waar het staat.

**Live:** https://effectory-ux.github.io/prototypes/

## Hoe het werkt

- `prototypes.json` is de lijst. Per prototype staat er één entry met de beginpagina,
  de eigenaar en in welke repo het leeft.
- `build-gallery.py` leest die lijst, haalt via de GitHub API op welke pagina's er in
  elke repo staan, en schrijft `index.html` uit `template.html`.
- Thumbnails zijn geen plaatjes maar de echte pagina in een verkleinde iframe, pas
  geladen als de kaart in beeld komt. Ze zijn dus altijd actueel.

## Een naam wijzigen vanaf de pagina

Klik op het potloodje naast een kaartnaam en typ een nieuwe. Je ziet het meteen,
maar alleen bij jezelf: de wijziging staat in je eigen browser (`localStorage`).
GitHub Pages serveert alleen statische bestanden, dus er is geen server die het
voor iedereen kan bewaren.

Onderin verschijnt een balk met **Publiceren**. Die zet de bijgewerkte
`prototypes.json` op je klembord en opent de GitHub-editor. Alles selecteren,
plakken, commit, en binnen een minuut ziet iedereen de nieuwe namen. Zo blijft
`prototypes.json` de enige bron en staat elke naamswijziging in de historie.

**Ongedaan maken** wist je lokale wijzigingen en zet de namen terug op wat er
gepubliceerd is.

## Een prototype toevoegen

1. Voeg een entry toe aan `entries` in `prototypes.json`:

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

`path` is de pagina die de kaart opent. Zet hier de nieuwste versie, want dat is wat
iemand ziet als hij op de thumbnail klikt. `also` claimt de overige schermen van
hetzelfde prototype, zodat het één kaart blijft in plaats van vijf losse.

Heeft één prototype meerdere ingangen, bijvoorbeeld dezelfde flow met andere data
of een andere ontwerprichting, dan zet je die als `variants`. De kaart opent altijd
de eerste, en een knopje "N pagina's" opent een modal met de hele lijst:

```json
"variants": [
  { "label": "Novanta · Q2", "path": "novanta-before-overview.html" },
  { "label": "Novanta · Q3", "path": "novanta-after-overview.html" }
]
```

2. Draai het script en commit het resultaat:

```bash
./build-gallery.py && git commit -am "Nieuw prototype toegevoegd" && git push
```

Het script meldt aan het eind welke pagina's nog door geen enkele kaart worden
opgeëist. Zo blijft er niets onbedoeld buiten de galerij vallen.

## Een repo toevoegen

Zet hem in `repos` in `prototypes.json`, met de Pages-URL als die er is:

```json
"mijn-repo": {
  "repo": "effectory-ux/mijn-repo",
  "pages": "https://effectory-ux.github.io/mijn-repo/",
  "repos": [{ "org": "effectory-ux", "name": "mijn-repo" }],
  "ignore": ["^404\\.html$"]
}
```

Laat je `variants` weg terwijl een prototype meer pagina's heeft, dan verzint de
generator de labels uit de bestandsnamen: het deel dat alle namen delen gaat eraf,
dus `group-linking-bol.html` wordt "Bol".

Zonder Pages krijgt de kaart geen thumbnail maar een link naar de code.
Gebruik `liveRewrite` als de repo een submap als site-root publiceert, zoals `cyos` doet
met `site/`.

## Waar staat wat

| Repo | Inhoud |
|---|---|
| [effectory-ux/Engage-Design-system-](https://github.com/effectory-ux/Engage-Design-system-) | het design system: componenten, tokens, iconen, skill |
| [effectory-design/effectory-design-documentation](https://github.com/effectory-design/effectory-design-documentation) | de prototypes van Jente |
| [eray-effectory/action-center](https://github.com/eray-effectory/action-center) | Action Center van Eray, nog zonder Pages |
| [eray-effectory/ux](https://github.com/eray-effectory/ux) | platform design van Eray |
| [effectory-ux/cyos](https://github.com/effectory-ux/cyos) | CYOS survey creation, fase 1 en 2 |
| [N33G3K/cyos-survey-creation-flow-demo](https://github.com/N33G3K/cyos-survey-creation-flow-demo) | losse CYOS-demo van Jamal |

`tokens.css` en `foundation.css` zijn kopieën uit het design system, zodat deze pagina
dezelfde kleuren en spacing gebruikt.

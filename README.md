# Projects · Effectory UX

Central entry point for every prototype the UX team builds, across repos and accounts.
One card per prototype, with a live thumbnail. The button on a card opens a dialog
listing all its pages and the repo it lives in.

**Live:** https://effectory-ux.github.io/prototypes/

## How it works

- `prototypes.json` is the list. One entry per prototype, naming its entry page, its
  owner and the repo it lives in.
- `build-gallery.py` reads that list, asks the GitHub API which pages each repo holds,
  and writes `index.html` from `template.html`.
- Thumbnails are not images but the real page in a scaled-down iframe, loaded only once
  the card comes near the viewport, so they are never stale.
- Styling comes from the [design system](https://effectory-ux.github.io/Engage-Design-system-/):
  tokens, components and the icon library are loaded from its site, not copied.

## Sections

Sections follow the three Product & Tech tracks: **Surveying**, **Leadership enablement**
and **Reporting**. Anything that touches none of them sits under **Platform**. A prototype
belongs to the track it is about, not the track of whoever made it: group linking is
Jente's but belongs to Surveying.

## Renaming from the page

Click the pencil next to a card name and type a new one. You see it immediately, but only
you do: the change lives in your browser (`localStorage`). GitHub Pages serves static files
only, so there is no server to keep it for everyone.

Names are read from `prototypes.json` at load, not from the generated `index.html`, so a
published name shows up without anyone running `build-gallery.py`.

A bar appears at the bottom with **Publish**. It copies the updated `prototypes.json` to
your clipboard and opens the GitHub editor. Select all, paste, commit, and everyone sees
the new names within a minute. That keeps `prototypes.json` the single source of truth and
puts every rename in the history.

**Undo** clears your local changes and puts the published names back.

### Without the publish step

Set a URL in `sync.url` in `prototypes.json` and a rename saves straight away for everyone,
dropping the publish step. `worker/` holds that endpoint plus deploy notes; it is one `GET`
and one `PUT`, so it can run somewhere other than Cloudflare. While `sync.url` is empty the
page never calls it and behaves as described above.

## Adding a prototype

1. Add an entry to `entries` in `prototypes.json`:

```json
{
  "name": "My prototype",
  "desc": "One line about what it shows.",
  "owner": "Jente",
  "group": "Reporting",
  "repo": "engage",
  "path": "prototypes/my-prototype.html",
  "also": ["^prototypes/my-prototype-"]
}
```

`path` is the page the card opens; point it at the newest version, because that is what
someone sees when they click the thumbnail. `also` claims the prototype's other screens so
it stays one card instead of five.

Does one prototype have several entry points, the same flow with different data or another
design direction? List them as `variants`. The card opens the first, and an "N pages" button
opens a dialog with the full list:

```json
"variants": [
  { "label": "Novanta · Q2", "path": "novanta-before-overview.html" },
  { "label": "Novanta · Q3", "path": "novanta-after-overview.html" }
]
```

2. Run the script and commit the result:

```bash
./build-gallery.py && git commit -am "Add a prototype" && git push
```

At the end the script reports any page no card claims yet, so nothing quietly stays out of
the gallery.

## Adding a repo

Put it in `repos` in `prototypes.json`, with its Pages URL if it has one:

```json
"my-repo": {
  "repo": "effectory-ux/my-repo",
  "pages": "https://effectory-ux.github.io/my-repo/",
  "repos": [{ "org": "effectory-ux", "name": "my-repo" }],
  "ignore": ["^404\\.html$"]
}
```

Leave `variants` out and the generator derives labels from the filenames, dropping the part
they all share, so `group-linking-bol.html` becomes "Bol".

Without Pages a card gets no thumbnail, just a link to the code. Use `liveRewrite` when a
repo publishes a subfolder as its site root, the way `cyos` does with `site/`.

## Where things live

| Repo | Content |
|---|---|
| [effectory-ux/Engage-Design-system-](https://github.com/effectory-ux/Engage-Design-system-) | the design system: components, tokens, icons, documentation, skill |
| [effectory-ux/group-linking](https://github.com/effectory-ux/group-linking) | the five group linking variants, ROC included |
| [effectory-ux/gtma](https://github.com/effectory-ux/gtma) | the GTMA before/after prototype, 24 screens |
| [effectory-design/effectory-design-documentation](https://github.com/effectory-design/effectory-design-documentation) | what has not moved yet: six prototypes plus Eray's Action Center and Conversation Guide |
| [eray-effectory/action-center](https://github.com/eray-effectory/action-center) | Eray's Action Center, no Pages yet |
| [eray-effectory/ux](https://github.com/eray-effectory/ux) | Eray's platform design |
| [effectory-ux/cyos](https://github.com/effectory-ux/cyos) | CYOS survey creation, phase 1 and 2 |
| [N33G3K/cyos-survey-creation-flow-demo](https://github.com/N33G3K/cyos-survey-creation-flow-demo) | Jamal's standalone CYOS demo |

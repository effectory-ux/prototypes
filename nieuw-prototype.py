#!/usr/bin/env python3
"""Voeg een prototype toe aan de galerij, zonder iets van iemand anders te raken.

    ./nieuw-prototype.py

Het script stelt een paar vragen, maakt een eigen branch, schrijft één nieuw
bestand in data/prototypes/, controleert het en zet er een pull request op.
Omdat het altijd een nieuw bestand op een nieuwe branch is, kan het per definitie
niet botsen met waar een ander op dat moment aan werkt.
"""

import glob
import json
import os
import re
import subprocess
import sys
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(ROOT, "data")


def run(*cmd, capture=False):
    r = subprocess.run(cmd, text=True, capture_output=capture)
    if r.returncode != 0:
        if capture:
            print(r.stdout, r.stderr, file=sys.stderr)
        sys.exit(f"\n✗ mislukt: {' '.join(cmd)}")
    return (r.stdout or "").strip()


def ask(vraag, verplicht=True, default=None):
    hint = f" [{default}]" if default else ""
    while True:
        antwoord = input(f"{vraag}{hint}: ").strip()
        if not antwoord and default:
            return default
        if antwoord or not verplicht:
            return antwoord
        print("  ↳ dit veld is verplicht")


def kies(vraag, opties):
    print(f"\n{vraag}")
    for i, o in enumerate(opties, 1):
        print(f"  {i}. {o}")
    while True:
        raw = input("Nummer: ").strip()
        if raw.isdigit() and 1 <= int(raw) <= len(opties):
            return opties[int(raw) - 1]
        print("  ↳ kies een nummer uit de lijst")


def slug(naam):
    s = unicodedata.normalize("NFKD", naam).encode("ascii", "ignore").decode()
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    os.chdir(ROOT)

    if run("git", "status", "--porcelain", capture=True):
        sys.exit(
            "✗ je hebt nog niet-gecommitte wijzigingen.\n"
            "  Commit of stash die eerst, dan begint dit script met een schone lei."
        )

    with open(os.path.join(DATA, "site.json")) as f:
        groepen = json.load(f)["groups"]
    repo_keys = sorted(
        os.path.basename(p)[:-5] for p in glob.glob(os.path.join(DATA, "repos", "*.json"))
    )

    print("Nieuw prototype toevoegen\n" + "-" * 25)
    naam = ask("Naam op de kaart")
    bestand = os.path.join(DATA, "prototypes", f"{slug(naam)}.json")
    if os.path.exists(bestand):
        sys.exit(f"✗ {os.path.relpath(bestand, ROOT)} bestaat al · kies een andere naam")

    desc = ask("Eén regel over wat het laat zien")
    owner = ask("Wie is de eigenaar", default=run("git", "config", "user.name", capture=True))
    group = kies("In welke groep hoort het?", groepen)
    repo = kies("In welke repo staat de pagina?", repo_keys)
    path = ask("Pad naar de beginpagina in die repo (bijv. prototypes/mijn-ding.html)")
    also = ask(
        "Patroon dat de overige schermen opeist (leeg = geen)",
        verplicht=False,
        default="",
    )

    entry = {
        "name": naam,
        "desc": desc,
        "owner": owner,
        "group": group,
        "repo": repo,
        "path": path,
    }
    if also:
        entry["also"] = [also]

    print("\n" + json.dumps(entry, ensure_ascii=False, indent=2))
    if input("\nZo goed? [j/N] ").strip().lower() not in ("j", "ja", "y"):
        sys.exit("Niets gedaan.")

    branch = f"prototype/{slug(naam)}"
    run("git", "fetch", "origin", "main", capture=True)
    run("git", "switch", "-c", branch, "origin/main", capture=True)

    with open(bestand, "w") as f:
        json.dump(entry, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("\nControleren")
    if subprocess.run([sys.executable, "build-gallery.py", "--check"]).returncode != 0:
        print(
            f"\n✗ de data klopt nog niet. Pas {os.path.relpath(bestand, ROOT)} aan,"
            "\n  draai ./build-gallery.py --check tot het groen is en commit dan zelf."
            f"\n  Je zit nu op branch {branch}."
        )
        sys.exit(1)

    run("git", "add", bestand, capture=True)
    run("git", "commit", "-m", f"Prototype toegevoegd: {naam}", capture=True)

    print(f"\nKlaar om te pushen: branch {branch}, één nieuw bestand.")
    if input("Pull request openen op GitHub? [j/N] ").strip().lower() not in ("j", "ja", "y"):
        print(f"Gecommit maar niet gepusht. Zelf doen: git push -u origin {branch}")
        return

    run("git", "push", "-u", "origin", branch)
    url = run(
        "gh", "pr", "create",
        "--title", f"Prototype toegevoegd: {naam}",
        "--body", f"{desc}\n\nToegevoegd met `./nieuw-prototype.py`.",
        capture=True,
    )
    print(f"\n✓ {url}\n  Merge hem zodra de check groen is; de galerij bouwt zichzelf.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nAfgebroken.")

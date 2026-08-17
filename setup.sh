#!/bin/sh
# Eenmalig per laptop. Git kan hooks niet zelf uit een repo installeren,
# vandaar dit regeltje.
set -e

cd "$(dirname "$0")"
git config core.hooksPath .githooks
chmod +x .githooks/* build-gallery.py nieuw-prototype.py 2>/dev/null || true

echo "✓ Klaar."
echo "  Je wordt nu gewaarschuwd als je per ongeluk op main commit."
echo "  Nieuw prototype toevoegen: ./nieuw-prototype.py"

"""Build Veil without replacing the earlier permissioned research browsers."""

import argparse
from build_pointer_browser import build
from run_native import ROOT

NAME = 'Veil'
APP = ROOT / 'dist/Veil.app'
MANIFEST = ROOT / 'docs/evidence/veil-browser-manifest.json'


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--replace-ungranted', action='store_true')
    args = parser.parse_args()
    build(args.replace_ungranted, name=NAME, app_path=APP, manifest_path=MANIFEST,
          identifier='research.agentfreebrowser.veil', extra_defines=['VEIL_BROWSER'])

#!/usr/bin/env python3
"""Télécharge les N dépôts GitHub les plus étoilés, filtrés par licence. Voir README.md."""
import argparse
import json
import os
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

GITHUB_API_URL = "https://api.github.com/search/repositories"
DEFAULT_REPO_COUNT = 10
DEFAULT_DEST_DIR = "./download"
REQUEST_TIMEOUT = 10
CLONE_WORKERS = 3


def fetch_top_repos(license_spdx: str, language: str, min_stars: int, count: int, token: str | None) -> list[dict]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "star-repo-cloner",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"

    query = f"license:{license_spdx} stars:>{min_stars}"
    if language:
        query += f" language:{language}"
    results: list[dict] = []
    page = 1
    # Taille de page fixe : GitHub calcule le décalage avec per_page, la changer
    # d'une page à l'autre renverrait des dépôts déjà reçus.
    per_page = min(100, count)

    while len(results) < count:
        params = {
            "q": query,
            "sort": "stars",
            "order": "desc",
            "per_page": str(per_page),
            "page": str(page),
        }
        url = GITHUB_API_URL + "?" + urllib.parse.urlencode(params)
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=REQUEST_TIMEOUT) as resp:
                data = json.loads(resp.read().decode())
        except urllib.error.HTTPError as e:
            print(f"Erreur API GitHub ({e.code}): {e.read().decode(errors='ignore')}", file=sys.stderr)
            if e.code == 403:
                print("→ Rate limit atteint. Ajoute --token ou attends un peu.", file=sys.stderr)
            sys.exit(1)
        except urllib.error.URLError as e:
            print(f"Impossible de joindre l'API GitHub : {e.reason}", file=sys.stderr)
            sys.exit(1)

        items = data.get("items", [])
        if not items:
            break

        results.extend(items)
        page += 1
        if page * per_page > 1000 or len(results) >= count:  # l'API ne renvoie que 1000 résultats
            break
        time.sleep(1)

    return results[:count]


def clone_repo(repo: dict, dest_dir: Path) -> bool:
    full_name = repo["full_name"]
    stars = repo["stargazers_count"]
    license_name = (repo.get("license") or {}).get("spdx_id", "?")
    target_path = dest_dir / full_name.replace("/", "__")

    if (target_path / ".git").exists():
        print(f"⏭  {full_name} déjà présent, on passe.")
        return True

    print(f"⬇️  Clonage de {full_name} ({stars:,} ⭐, licence {license_name})...")
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo["clone_url"], str(target_path)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"❌ Échec du clonage de {full_name}: {result.stderr.strip()}", file=sys.stderr)
        return False

    print(f"✅ {full_name} cloné dans {target_path}")
    return True


def main():
    # Émojis dans la console Windows (cp1252) même quand la sortie est redirigée.
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
    parser = argparse.ArgumentParser(description="Télécharge les N dépôts GitHub les plus étoilés, filtrés par licence.")
    parser.add_argument("--license", default="mit", help="Licence SPDX : mit, apache-2.0, bsd-2-clause, bsd-3-clause, mpl-2.0, unlicense (défaut: mit)")
    parser.add_argument("--language", default="", help="Langage principal du code (ex: python, javascript, rust) — optionnel, aucun filtre par défaut")
    parser.add_argument("--min-stars", type=int, default=100, help="Seuil minimum d'étoiles (défaut: 100) — à baisser pour un langage/licence rare sans résultat")
    parser.add_argument("--count", type=int, default=DEFAULT_REPO_COUNT, help=f"Nombre de dépôts (défaut: {DEFAULT_REPO_COUNT})")
    parser.add_argument("--dest", default=DEFAULT_DEST_DIR, help=f"Dossier de destination (défaut: {DEFAULT_DEST_DIR})")
    parser.add_argument("--token", default=os.environ.get("GITHUB_TOKEN"), help="Token GitHub, aucun scope requis (ou variable d'env GITHUB_TOKEN) — https://github.com/settings/tokens")
    parser.add_argument("--dry-run", action="store_true", help="Affiche les dépôts trouvés sans les cloner")
    args = parser.parse_args()

    if shutil.which("git") is None:
        print(
            "Erreur : Git n'est pas installé sur ton système.\n"
            "Télécharge-le ici : https://git-scm.com/downloads\n"
            "Puis relance ce script.",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.count < 1:
        print("--count doit être un nombre entier ≥ 1", file=sys.stderr)
        sys.exit(1)

    dest_dir = Path(args.dest)
    dest_dir.mkdir(parents=True, exist_ok=True)

    language_filter = f" en {args.language}" if args.language else ""
    print(f"🔍 Recherche des {args.count} dépôts les plus étoilés{language_filter} avec la licence '{args.license}'...\n")
    repos = fetch_top_repos(args.license, args.language, args.min_stars, args.count, args.token)
    if not repos:
        print("Aucun dépôt trouvé. Vérifie le nom de la licence (ex: mit, apache-2.0, bsd-3-clause) et du langage.")
        sys.exit(1)

    print(f"Trouvé {len(repos)} dépôt(s). Détails :\n")
    for i, repo in enumerate(repos, 1):
        license_name = (repo.get("license") or {}).get("spdx_id", "?")
        print(f"  {i:2d}. {repo['full_name']:40s} ⭐ {repo['stargazers_count']:>8,}  ({license_name})")
    print()

    if args.dry_run:
        print("Dry-run : rien n'a été cloné.")
        return

    with ThreadPoolExecutor(max_workers=CLONE_WORKERS) as pool:
        successes = sum(pool.map(lambda repo: clone_repo(repo, dest_dir), repos))

    print(f"\n🎉 Terminé : {successes}/{len(repos)} dépôts clonés dans {dest_dir.resolve()}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nInterrompu.", file=sys.stderr)
        sys.exit(130)

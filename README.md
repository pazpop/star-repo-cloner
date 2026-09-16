![star-repo-cloner](assets/banner.svg)

# star-repo-cloner

Ce petit programme va sur [GitHub](https://github.com) et télécharge
automatiquement sur ton ordinateur les projets les plus populaires (les plus
"étoilés" ⭐) qui utilisent une certaine licence.

Par défaut, il télécharge les **10 projets les plus populaires en licence
MIT**.

## Installation

Il te faut deux programmes installés sur ton ordinateur : **Python** (pour
exécuter le script) et **Git** (que le script utilise pour télécharger les
projets). On installe les deux avec `winget`, un installateur déjà intégré à
Windows 11.

1. Ouvre **PowerShell** (cherche "PowerShell" dans le menu Démarrer de
   Windows, puis clique dessus).
2. Copie-colle cette ligne dans la fenêtre qui s'ouvre, puis appuie sur
   Entrée :
   ```powershell
   winget install --id Python.Python.3.13 -e
   ```
3. Une fois terminé, installe Git de la même façon :
   ```powershell
   winget install --id Git.Git -e
   ```
4. **Ferme puis rouvre PowerShell** (nécessaire pour que Windows retrouve
   les nouveaux programmes installés).
5. Vérifie que tout est bien installé :
   ```powershell
   python --version
   git --version
   ```
   Tu dois voir un numéro de version s'afficher pour chacun (ex: `Python
   3.13.0` et `git version 2.47.0`).

## Utilisation

1. Mets le fichier `star_repo_cloner.py` dans un dossier facile à
   retrouver (ex: `Documents\star-repo-cloner`).
2. Ouvre PowerShell (comme à l'étape d'installation).
3. Déplace-toi dans ce dossier. Exemple, si tu l'as mis dans
   `Documents\star-repo-cloner` :
   ```
   cd Documents\star-repo-cloner
   ```
4. Lance le programme :
   ```
   python star_repo_cloner.py
   ```
5. Laisse-le travailler. Il affiche ce qu'il fait au fur et à mesure, puis
   un résumé à la fin. Les projets téléchargés se retrouvent dans un
   nouveau dossier `download`, juste à côté du script.

### Personnaliser (facultatif)

- Télécharger un autre nombre de projets (ex: 20) :
  ```
  python star_repo_cloner.py --count 20
  ```
- Choisir une autre licence (ex: Apache 2.0) :
  ```
  python star_repo_cloner.py --license apache-2.0
  ```
  Licences courantes : `mit`, `apache-2.0`, `bsd-2-clause`, `bsd-3-clause`,
  `mpl-2.0`, `unlicense`.
  Pour comprendre ce que chacune signifie : [Licence de logiciel permissive — Wikipédia](https://fr.wikipedia.org/wiki/Licence_de_logiciel_permissive).
- Filtrer par langage de programmation (ex: Python) :
  ```
  python star_repo_cloner.py --language python
  ```
- Baisser le seuil minimum d'étoiles (par défaut 100) si une combinaison
  licence/langage rare ne donne aucun résultat :
  ```
  python star_repo_cloner.py --language cobol --min-stars 10
  ```
- Voir quels dépôts seraient trouvés sans rien télécharger (pratique pour
  ajuster les filtres avant de lancer un vrai téléchargement) :
  ```
  python star_repo_cloner.py --dry-run
  ```
  Toutes ces options sont combinables entre elles et avec `--count`.

## Limitations à connaître

- **Ça prend de la place.** Certains projets populaires peuvent peser
  plusieurs centaines de Mo, voire plus. Vérifie que tu as de l'espace
  disque disponible.
- **Besoin d'internet**, évidemment — le script télécharge tout depuis
  GitHub.
- **Limite de GitHub sans "jeton" (token)** : sans configuration
  supplémentaire, GitHub limite le nombre de recherches qu'on peut faire par
  minute. Pour une dizaine de projets, ça ne pose aucun problème. Si tu vois
  une erreur mentionnant une "limite atteinte" (rate limit), attends
  quelques minutes puis relance. Sinon, il faut créer un token GitHub (voir
  `python star_repo_cloner.py --help`, option `--token`).
- **Relancer le script ne re-télécharge pas ce qui est déjà là** : les
  projets déjà présents dans `download` sont simplement ignorés
  (message "déjà présent, on passe").
- **La licence et le langage affichés par GitHub ne sont pas toujours
  fiables à 100 %** : GitHub les détecte automatiquement à partir des
  fichiers du projet — dans de rares cas, un projet peut être mal classé.
- **Une faute de frappe dans `--language` ne donne aucune erreur.** Testé
  empiriquement : GitHub ignore silencieusement une valeur de langage
  inconnue (ex: `--language phyton` au lieu de `python`) et renvoie les
  mêmes résultats que sans filtre du tout, sans avertissement. Vérifie
  toujours l'orthographe du langage.

## Licence

[MIT](LICENSE).

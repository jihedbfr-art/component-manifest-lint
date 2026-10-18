<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="120" height="120">
</p>

# component-manifest-lint

[English version](README.md)

Vérifie un manifeste de composant télécom (la ressource Kubernetes `Component` du Canvas de l'Open Digital Architecture) avant qu'il n'atteigne un cluster : champs inconnus ou mal orthographiés, champs obligatoires absents, mauvais types, et incohérences entre le manifeste et ses propres services. Hors ligne, une seule dépendance (PyYAML), sans IA.

> Projet indépendant. Sans affiliation, approbation ni certification de TM Forum. Un résultat propre ne dit rien de la conformité ni d'une certification.

## Pourquoi cet outil

Le schéma publié d'un `Component` a peu de champs obligatoires et ne conserve pas les champs inconnus : un `exposedApis` mal écrit n'est donc pas une erreur, le cluster l'ignorera très probablement, et on s'en aperçoit quand le composant n'expose pas ce qu'on avait écrit. L'outil lit le même schéma publié et vous prévient avant le déploiement. Il vérifie aussi ce que le schéma ne peut pas vérifier : que `implementation` désigne un vrai Service et que le port correspond, que les noms d'API sont uniques, que les URL de spécification ne suivent pas une branche mouvante.

## Démarrage rapide

Python 3.10 ou plus et PyYAML :

```bash
git clone https://github.com/jihedbfr-art/component-manifest-lint.git
cd component-manifest-lint
pip install pyyaml
PYTHONPATH=src python -m component_manifest_lint --lang fr fixtures/order-desk.weak.yaml
```

Ou `pip install .` puis `component-manifest-lint FICHIER [FICHIER ...]`. Plusieurs documents par fichier sont acceptés ; seuls les documents `kind: Component` sont contrôlés (dans un fichier à plusieurs composants, les constats portent le numéro du document, `fichier#N`), et les Services du même fichier servent aux recoupements. Une valeur nulle compte comme absente, puisque le cluster élague les nulls. Les clés dupliquées dans un mapping sont refusées. Un modèle Helm doit d'abord être rendu (`helm template`) : l'outil refuse les fichiers qui contiennent encore `{{`.

Options : `--lang en|fr` (constats et libellés du rapport ; les erreurs de lecture et d'analyse restent en anglais), `--format text|json|md|sarif`, `--fail-on error|warn|never` (défaut `error`). Codes de sortie : `0` quand aucun constat n'atteint le niveau `--fail-on`, `1` sinon, `2` pour un fichier illisible ou invalide.

## Sortie SARIF

`--format sarif` produit du JSON SARIF 2.1.0. Les douze règles ont une description anglaise ; les messages des constats suivent `--lang`. Les niveaux `error`, `warn`, `info` deviennent `error`, `warning`, `note`. Chaque constat contient l'URI du fichier et un chemin logique préfixé par l'indice du document YAML, compté à partir de zéro. Aucun numéro de ligne n'est deviné. Les fichiers sous le répertoire courant utilisent une URI relative encodée ; les fichiers externes utilisent une URI de fichier absolue. Lancez la commande depuis la racine du dépôt pour un rapport portable.

Copiez ce fragment de job dans votre propre workflow GitHub Actions après avoir choisi un runner. Il installe le dépôt extrait et contrôle une fixture fournie ; remplacez son chemin par celui de votre manifeste. Le téléversement s'exécute aussi quand des constats provoquent le code 1, et le contrôle reste en échec. Les erreurs de lecture ou d'analyse (code 2) empêchent le téléversement et restent des échecs. Il s'agit seulement d'un exemple documentaire ; les workflows du dépôt restent inchangés. Cette modification n'a pas été testée par un téléversement réel ni par l'affichage d'alertes dans GitHub.

```yaml
permissions:
  contents: read
  security-events: write
steps:
  - uses: actions/checkout@v6
  - run: pip install .
  - name: Check manifests
    id: manifest
    shell: bash
    run: |
      set +e
      component-manifest-lint fixtures/order-desk.weak.yaml --format sarif > results.sarif
      status=$?
      echo "status=$status" >> "$GITHUB_OUTPUT"
      exit "$status"
  - name: Upload SARIF
    if: ${{ !cancelled() && (steps.manifest.outputs.status == '0' || steps.manifest.outputs.status == '1') }}
    uses: github/codeql-action/upload-sarif@v4
    with:
      sarif_file: results.sarif
      category: component-manifest-lint
```

Références (consultées le 18 octobre 2026) : [documentation GitHub du téléversement SARIF](https://docs.github.com/en/code-security/how-tos/find-and-fix-code-vulnerabilities/integrate-with-existing-tools/upload-sarif-file), [schéma SARIF 2.1.0](https://json.schemastore.org/sarif-2.1.0.json).


## Ce qui est contrôlé

| Règle | Niveau | Fondée sur | Contrôle |
|---|---|---|---|
| M001 | avert. | schéma publié | un champ que le schéma de cette `apiVersion` ne définit pas |
| M002 | avert. | schéma publié | `apiVersion` n'est pas l'une des versions publiées (`v1`, `v1beta2`, `v1beta3`, `v1beta4`) |
| M006 | erreur | schéma publié | un champ que le schéma déclare obligatoire est absent |
| M012 | erreur | schéma publié | un champ a le mauvais type (par exemple `dependentAPIs` est une chaîne) |
| M003 | info | deux exemples publics | le label `oda.tmforum.org/componentName` est égal à `metadata.name` |
| M004 | info | jugement | `componentMetadata` a id, name, version, description |
| M005 | avert. | jugement | `componentMetadata.version` ressemble à MAJEUR.MINEUR.CORRECTIF |
| M007 | avert. | cohérence | `implementation` désigne un Service du même fichier (seulement si le fichier a des Services) |
| M008 | avert. | cohérence | le `port` de l'API est l'un des ports de ce Service |
| M009 | info | deux exemples publics | le `path` de l'API commence par `/` + le nom du composant |
| M010 | avert. | cohérence | un nom d'API apparaît deux fois dans une même section de fonction |
| M011 | info | jugement | une URL de spécification pointe vers `master`, `main` ou `HEAD` au lieu d'un commit ou d'une étiquette |

Les preuves de chaque règle, et le commit d'où le schéma a été tiré, sont dans [docs/evidence.fr.md](docs/evidence.fr.md).

## Limites

- Contrôles statiques de fichiers. Ni cluster, ni webhook d'admission, ni réseau : un Canvas en marche peut accepter ou rejeter autrement.
- Le fichier de schéma du paquet est un instantané (voir la page de preuves). Régénérez-le avec `tools/extract_schema.py` quand le schéma publié change.
- Les parties libres du schéma (comme la gestion des secrets) ne sont pas contrôlées à l'intérieur.
- Les règles de jugement sont des suggestions ; avec `--fail-on error`, seules les erreurs de schéma font échouer.

## Tests

```bash
python -m unittest discover -s tests
```

40 tests. Les jeux d'essai sont des manifestes inventés dans `fixtures/`.

## Parcours d'étude

Les idées derrière ces contrôles sont expliquées, avec sources et exercices, dans le parcours d'étude bilingue [oda-learning-lab](https://github.com/jihedbfr-art/oda-learning-lab/blob/main/docs/fr/05-les-composants-en-pratique.md) (module 5).

## Licence et contact

Code : [Apache License 2.0](LICENSE). Des fonctions avancées peuvent être discutées sur demande : voir [COMMERCIAL.fr.md](COMMERCIAL.fr.md).

---

<p align="center">
  <img src="assets/jihedailabs-logo.svg" alt="JihedAiLabs" width="80" height="80"><br>
  <sub>Conçu et maintenu sous <b>JihedAiLabs</b>.</sub>
</p>

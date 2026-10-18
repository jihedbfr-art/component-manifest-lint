# Historique des versions

[English version](CHANGELOG.md)

## 0.2.0

Ajout de la sortie SARIF 2.1.0 : descriptions des règles en anglais, constats traduits, URI des fichiers et chemins logiques des documents. Codes de sortie inchangés. Exemple GitHub Actions à copier pour le téléversement, sans modification des workflows. 40 tests.

## 0.1.1

Corrections issues d'une revue indépendante, reproduites avant correction : gestion des types incorrects pour `implementation` et `specification`, des API sans nom et des Services malformés ; valeurs nulles traitées comme absentes ; champs obligatoires contrôlés dans les objets libres ; acceptation de `status` à la racine ; correspondance des Services par namespace et signalement des ports absents (M008) ; M011 limité aux URL GitHub raw/blob suivant une branche mouvante ; refus des clés YAML dupliquées ; numéros de documents fidèles au fichier et visibles pour plusieurs Components. 33 tests.

## 0.1.0

Première version : douze contrôles sur les manifestes Component (schéma, cohérence et suggestions), messages en anglais et français, sorties texte/JSON/Markdown, extracteur de schéma, 18 tests.

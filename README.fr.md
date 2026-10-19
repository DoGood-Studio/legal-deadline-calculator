<p align="center">
  <a href="README.md">English</a> · <a href="README.tr.md">Türkçe</a> · <a href="README.de.md">Deutsch</a> · <strong>Français</strong> · <a href="README.es.md">Español</a> · <a href="README.it.md">Italiano</a> · <a href="README.pt.md">Português</a> · <a href="README.nl.md">Nederlands</a> · <a href="README.ru.md">Русский</a> · <a href="README.ar.md">العربية</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo-dark.svg">
    <img alt="" src="docs/images/logo.svg" width="72" height="72">
  </picture>
</p>

<h1 align="center">lexdays</h1>

<p align="center">
  <strong>Des délais de procédure vérifiables.</strong><br>
  Le dernier jour pour agir, chaque étape expliquée, avec le texte ou la décision de justice qui la fonde.
</p>

<p align="center">
  <a href="https://github.com/DoGood-Studio/legal-deadline-calculator/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/DoGood-Studio/legal-deadline-calculator/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/lexdays/"><img alt="PyPI" src="https://img.shields.io/pypi/v/lexdays?color=1e3a5c"></a>
  <a href="https://www.npmjs.com/package/lexdays"><img alt="npm" src="https://img.shields.io/npm/v/lexdays?color=1e3a5c"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-1e3a5c"></a>
</p>

<p align="center">
  <a href="https://dogood-studio.github.io/legal-deadline-calculator/?lang=fr"><strong>Démo en ligne</strong></a> ·
  <a href="docs/usage.md">Documentation (en anglais)</a> ·
  <a href="docs/verification.md">Rapport de vérification (en anglais)</a>
</p>

<p align="center">
  <a href="https://dogood-studio.github.io/legal-deadline-calculator/?lang=fr">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/images/hero-fr-dark.png">
      <img alt="La démo de lexdays en français : délai de recours devant la Cour de justice de l'UE à compter d'une publication au Journal officiel, avec le calendrier et la justification de chaque étape." src="docs/images/hero-fr-light.png" width="860">
    </picture>
  </a>
</p>

Les bibliothèques de jours fériés indiquent quels jours sont fériés. lexdays indique **le dernier jour pour déposer, signifier ou payer, et pourquoi**. Chaque résultat énumère les étapes suivies, par exemple les vacances judiciaires, le report dû à un jour férié ou une signification réputée faite, et la règle qui fonde chacune.

Dans la démo, un clic ajoute le dernier jour à votre calendrier, et le fichier de calendrier vous le rappelle trois jours puis un jour avant.

## Démarrage rapide

```bash
pip install lexdays        # Python 3.10+
npm install lexdays        # Node 18+, navigateurs, Deno, Bun
```

```python
import lexdays

r = lexdays.compute("us/frcp", "2025-07-31", "P30D")   # tribunal fédéral américain : 30 jours
r.deadline              # datetime.date(2025, 9, 2): samedi 30 août et Labor Day : reporté au mardi
print(r.explain("fr"))  # chaque étape, avec sa source
```

<details>
<summary><strong>TypeScript</strong></summary>

```ts
import { compute } from "lexdays";

const r = compute("us/frcp", "2025-07-31", "P30D");
r.deadline;          // "2025-09-02"
r.explain("fr");     // les étapes expliquées en français
```

</details>

<details>
<summary><strong>Ligne de commande</strong></summary>

```bash
lexdays deadline us/frcp 2025-07-31 P30D --lang fr
```

</details>

Plus d'exemples, toutes les options et l'API : [docs/usage.md](docs/usage.md) (en anglais).

## Ce qui est couvert

| Juridiction | Paquets de règles | Ce qui est modélisé |
|---|---|---|
| Turquie | `tr/hmk` `tr/iik` `tr/cmk` `tr/iyuk` `tr/vuk` `tr/aym` | Vacances judiciaires et pause estivale des juridictions administratives, veilles de fête, notification électronique au cinquième jour, fins de mois |
| États-Unis | `us/frcp` | FRCP 6(a) en avant et à rebours, 6(d) trois jours supplémentaires, jours fériés des États |
| Angleterre et pays de Galles | `gb-eaw/cpr` | Jours francs, délais courts, signification réputée faite (CPR 6.14, 6.26), fermeture des greffes |
| Cour de justice de l'UE | `eu/cj` | Publication au Journal officiel, délai de distance de dix jours, e-Curia |
| Allemagne | `de/zpo` | § 222 ZPO avec les §§ 187–188 BGB, jours fériés de chaque Land, d'Augsbourg et de la Bavière catholique |

24 calendriers de jours fériés aux années vérifiées · étapes de calcul expliquées en 12 langues · résultats identiques en Python et en TypeScript.

## Pourquoi se fier à un résultat

- **Chaque étape cite sa source**, l'article de loi ou la décision de justice, avec un lien.
- **Les points controversés sont des options**, et le résultat comporte une remarque. Les valeurs par défaut suivent la jurisprudence établie de la cour suprême, sinon la date la plus précoce.
- **Rien n'est deviné.** Une date hors des données vérifiées provoque une erreur plutôt qu'un jour erroné.
- **Vérifié sous plusieurs angles.**
  - 331 cas de test écrits à la main, dont beaucoup tirés de décisions de justice et d'exemples officiels.
  - Python et TypeScript doivent concorder sur 1 800 cas aléatoires.
  - Les calendriers sont comparés à des données indépendantes.
  - Chaque règle a été contrôlée sur ses sources avant la publication ([rapport](docs/verification.md)).

## En 12 langues, sur tous les écrans

<p align="center">
  <img width="30%" alt="Résultat sur téléphone en anglais : un délai fédéral américain avec trois jours ajoutés pour une signification par courrier." src="docs/images/phone-en.png">
  <img width="30%" alt="Résultat sur téléphone en arabe, de droite à gauche." src="docs/images/phone-ar.png">
  <img width="30%" alt="Résultat sur téléphone en japonais avec le thème sombre : un délai d'appel allemand selon le calendrier de Munich." src="docs/images/phone-ja.png">
</p>

## Contribuer

Les corrections et les relectures par des juristes sont les contributions les plus précieuses. Si un résultat est faux, ouvrez une [correction de règle](https://github.com/DoGood-Studio/legal-deadline-calculator/issues/new?template=rule-correction.yml) avec la source. Une nouvelle juridiction est un paquet de règles JSON accompagné de cas de test ; voir [CONTRIBUTING.md](CONTRIBUTING.md) et [docs/rulepacks.md](docs/rulepacks.md).

---

<sub>lexdays est un outil d'information, pas un conseil juridique. La loi, la jurisprudence, les décisions de justice et la pratique locale priment ; vérifiez toujours un délai important. [Licence MIT](LICENSE).</sub>

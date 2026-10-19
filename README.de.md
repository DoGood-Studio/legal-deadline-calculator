<p align="center">
  <a href="README.md">English</a> · <a href="README.tr.md">Türkçe</a> · <strong>Deutsch</strong> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.it.md">Italiano</a> · <a href="README.pt.md">Português</a> · <a href="README.nl.md">Nederlands</a> · <a href="README.ru.md">Русский</a> · <a href="README.ar.md">العربية</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo-dark.svg">
    <img alt="" src="docs/images/logo.svg" width="72" height="72">
  </picture>
</p>

<h1 align="center">lexdays</h1>

<p align="center">
  <strong>Rechtliche Fristen, nachvollziehbar berechnet.</strong><br>
  Der letzte Tag für eine Handlung, jeder Schritt erklärt, mit der Vorschrift oder Gerichtsentscheidung dahinter.
</p>

<p align="center">
  <a href="https://github.com/DoGood-Studio/legal-deadline-calculator/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/DoGood-Studio/legal-deadline-calculator/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/lexdays/"><img alt="PyPI" src="https://img.shields.io/pypi/v/lexdays?color=1e3a5c"></a>
  <a href="https://www.npmjs.com/package/lexdays"><img alt="npm" src="https://img.shields.io/npm/v/lexdays?color=1e3a5c"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-1e3a5c"></a>
</p>

<p align="center">
  <a href="https://dogood-studio.github.io/legal-deadline-calculator/?lang=de"><strong>Live-Demo</strong></a> ·
  <a href="docs/usage.md">Dokumentation (englisch)</a> ·
  <a href="docs/verification.md">Prüfbericht (englisch)</a>
</p>

<p align="center">
  <a href="https://dogood-studio.github.io/legal-deadline-calculator/?lang=de">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/images/hero-de-dark.png">
      <img alt="Die lexdays-Demo auf Deutsch: Berufungsfrist nach der ZPO an einem Münchner Gericht, mit Kalender und Begründung jedes Schritts." src="docs/images/hero-de-light.png" width="860">
    </picture>
  </a>
</p>

Feiertagsbibliotheken sagen, welche Tage Feiertage sind. lexdays sagt **den letzten Tag, um einzureichen, zuzustellen oder zu zahlen, und warum**. Jedes Ergebnis listet seine Schritte auf, etwa Gerichtsferien, die Verschiebung wegen eines Feiertags oder eine Zustellungsfiktion, und die Vorschrift hinter jedem Schritt.

## Schnellstart

```bash
pip install lexdays        # Python 3.10+
npm install lexdays        # Node 18+, Browser, Deno, Bun
```

```python
import lexdays

r = lexdays.compute("de/zpo", "2025-07-15", "P1M", calendar="de-by-catholic")   # Berufung (§ 517 ZPO), Gericht in München
r.deadline              # datetime.date(2025, 8, 18): der 15. August ist in München Feiertag
print(r.explain("de"))  # jeder Schritt mit Fundstelle
```

<details>
<summary><strong>TypeScript</strong></summary>

```ts
import { compute } from "lexdays";

const r = compute("de/zpo", "2025-07-15", "P1M", { calendar: "de-by-catholic" });
r.deadline;          // "2025-08-18"
r.explain("de");     // Erklärung auf Deutsch
```

</details>

<details>
<summary><strong>Kommandozeile</strong></summary>

```bash
lexdays deadline de/zpo 2025-07-15 P1M --calendar de-by-catholic --lang de
```

</details>

Weitere Beispiele, alle Optionen und die API: [docs/usage.md](docs/usage.md) (englisch).

## Was abgedeckt ist

| Rechtsordnung | Regelpakete | Was modelliert ist |
|---|---|---|
| Türkei | `tr/hmk` `tr/iik` `tr/cmk` `tr/iyuk` `tr/vuk` `tr/aym` | Gerichtsferien und Sommerpause der Verwaltungsgerichte, Vorabende von Feiertagen, elektronische Zustellung am fünften Tag, Monatsende |
| USA | `us/frcp` | FRCP 6(a) vorwärts und rückwärts, 6(d) drei zusätzliche Tage, Feiertage der Bundesstaaten |
| England und Wales | `gb-eaw/cpr` | Volle Tage (clear days), kurze Fristen, Zustellungsfiktion (CPR 6.14, 6.26), geschlossene Geschäftsstellen |
| Gerichtshof der EU | `eu/cj` | Veröffentlichung im Amtsblatt, zehn Tage Entfernungsfrist, e-Curia |
| Deutschland | `de/zpo` | § 222 ZPO mit §§ 187–188 BGB, Feiertage aller Länder sowie Augsburgs und des katholischen Bayerns |

24 Feiertagskalender mit geprüften Jahren · Rechenschritte in 12 Sprachen erklärt · identische Ergebnisse in Python und TypeScript.

## Warum Sie einem Ergebnis vertrauen können

- **Jeder Schritt nennt seine Quelle**, die Vorschrift oder die Gerichtsentscheidung, mit Link.
- **Strittige Punkte sind Optionen**, und das Ergebnis enthält einen Hinweis. Voreinstellungen folgen gefestigter höchstrichterlicher Rechtsprechung, sonst dem früheren Datum.
- **Es wird nicht geraten.** Daten außerhalb der geprüften Feiertagsdaten führen zu einem Fehler statt zu einem falschen Tag.
- **Mehrfach geprüft.**
  - 331 von Hand geschriebene Testfälle, viele aus Gerichtsentscheidungen und amtlichen Beispielen.
  - Python und TypeScript müssen in 1.800 Zufallsfällen übereinstimmen.
  - Die Kalender werden mit unabhängigen Daten abgeglichen.
  - Vor der Veröffentlichung wurde jede Regel an ihren Quellen geprüft ([Bericht](docs/verification.md)).

## In 12 Sprachen, auf jedem Bildschirm

<p align="center">
  <img width="30%" alt="Ergebnis auf dem Smartphone auf Englisch: eine US-Bundesfrist mit drei zusätzlichen Tagen für Zustellung per Post." src="docs/images/phone-en.png">
  <img width="30%" alt="Ergebnis auf dem Smartphone auf Arabisch, von rechts nach links." src="docs/images/phone-ar.png">
  <img width="30%" alt="Ergebnis auf dem Smartphone auf Japanisch im dunklen Design: eine deutsche Berufungsfrist mit dem Münchner Kalender." src="docs/images/phone-ja.png">
</p>

## Mitwirken

Korrekturen und Prüfungen durch Juristinnen und Juristen sind am wertvollsten. Wenn ein Ergebnis falsch ist, eröffnen Sie eine [Regelkorrektur](https://github.com/DoGood-Studio/legal-deadline-calculator/issues/new?template=rule-correction.yml) mit der Quelle. Eine neue Rechtsordnung ist ein JSON-Regelpaket mit Testfällen; siehe [CONTRIBUTING.md](CONTRIBUTING.md) und [docs/rulepacks.md](docs/rulepacks.md).

---

<sub>lexdays ist ein unverbindliches Hilfsmittel und keine Rechtsberatung. Gesetze, Rechtsprechung, gerichtliche Anordnungen und örtliche Praxis gehen vor; prüfen Sie jede wichtige Frist. [MIT-Lizenz](LICENSE).</sub>

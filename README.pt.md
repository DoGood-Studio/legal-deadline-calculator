<p align="center">
  <a href="README.md">English</a> · <a href="README.tr.md">Türkçe</a> · <a href="README.de.md">Deutsch</a> · <a href="README.fr.md">Français</a> · <a href="README.es.md">Español</a> · <a href="README.it.md">Italiano</a> · <strong>Português</strong> · <a href="README.nl.md">Nederlands</a> · <a href="README.ru.md">Русский</a> · <a href="README.ar.md">العربية</a> · <a href="README.zh.md">中文</a> · <a href="README.ja.md">日本語</a>
</p>

<p align="center">
  <picture>
    <source media="(prefers-color-scheme: dark)" srcset="docs/images/logo-dark.svg">
    <img alt="" src="docs/images/logo.svg" width="72" height="72">
  </picture>
</p>

<h1 align="center">lexdays</h1>

<p align="center">
  <strong>Prazos processuais verificáveis.</strong><br>
  O último dia para agir, cada passo explicado, com a norma ou a decisão judicial em que se baseia.
</p>

<p align="center">
  <a href="https://github.com/DoGood-Studio/legal-deadline-calculator/actions/workflows/ci.yml"><img alt="CI" src="https://github.com/DoGood-Studio/legal-deadline-calculator/actions/workflows/ci.yml/badge.svg"></a>
  <a href="https://pypi.org/project/lexdays/"><img alt="PyPI" src="https://img.shields.io/pypi/v/lexdays?color=1e3a5c"></a>
  <a href="https://www.npmjs.com/package/lexdays"><img alt="npm" src="https://img.shields.io/npm/v/lexdays?color=1e3a5c"></a>
  <a href="LICENSE"><img alt="MIT License" src="https://img.shields.io/badge/license-MIT-1e3a5c"></a>
</p>

<p align="center">
  <a href="https://dogood-studio.github.io/legal-deadline-calculator/?lang=pt"><strong>Demo online</strong></a> ·
  <a href="docs/usage.md">Documentação (em inglês)</a> ·
  <a href="docs/verification.md">Relatório de verificação (em inglês)</a>
</p>

<p align="center">
  <a href="https://dogood-studio.github.io/legal-deadline-calculator/?lang=pt">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="docs/images/hero-pt-dark.png">
      <img alt="A demo do lexdays em português: prazo de recurso para o Tribunal de Justiça da UE a contar de uma publicação no Jornal Oficial, com o calendário e a justificação de cada passo." src="docs/images/hero-pt-light.png" width="860">
    </picture>
  </a>
</p>

As bibliotecas de feriados dizem que dias são feriados. O lexdays diz **o último dia para apresentar, notificar ou pagar, e porquê**. Cada resultado lista os passos seguidos, como as férias judiciais, o adiamento por um feriado ou uma notificação presumida, e a norma em que cada um se baseia.

## Início rápido

```bash
pip install lexdays        # Python 3.10+
npm install lexdays        # Node 18+, navegadores, Deno, Bun
```

```python
import lexdays

r = lexdays.compute("us/frcp", "2025-07-31", "P30D")   # tribunal federal dos EUA: 30 dias
r.deadline              # datetime.date(2025, 9, 2): sábado, 30 de agosto, e Labor Day: passa para terça-feira
print(r.explain("pt"))  # cada passo, com a sua fonte
```

<details>
<summary><strong>TypeScript</strong></summary>

```ts
import { compute } from "lexdays";

const r = compute("us/frcp", "2025-07-31", "P30D");
r.deadline;          // "2025-09-02"
r.explain("pt");     // os passos explicados em português
```

</details>

<details>
<summary><strong>Linha de comandos</strong></summary>

```bash
lexdays deadline us/frcp 2025-07-31 P30D --lang pt
```

</details>

Mais exemplos, todas as opções e a API: [docs/usage.md](docs/usage.md) (em inglês).

## O que cobre

| Jurisdição | Pacotes de regras | O que é modelado |
|---|---|---|
| Turquia | `tr/hmk` `tr/iik` `tr/cmk` `tr/iyuk` `tr/vuk` `tr/aym` | Férias judiciais e pausa de verão dos tribunais administrativos, vésperas de feriado, notificação eletrónica ao quinto dia, fim do mês |
| Estados Unidos | `us/frcp` | FRCP 6(a) para a frente e para trás, 6(d) três dias adicionais, feriados estaduais |
| Inglaterra e País de Gales | `gb-eaw/cpr` | Dias completos, prazos curtos, notificação presumida (CPR 6.14, 6.26), encerramento das secretarias |
| Tribunal de Justiça da UE | `eu/cj` | Publicação no Jornal Oficial, dilação de dez dias em razão da distância, e-Curia |
| Alemanha | `de/zpo` | § 222 ZPO com os §§ 187–188 BGB, feriados de cada Land, de Augsburgo e da Baviera católica |

24 calendários de feriados com anos verificados · passos do cálculo explicados em 12 línguas · resultados idênticos em Python e TypeScript.

## Porque pode confiar num resultado

- **Cada passo indica a sua fonte**, o artigo da lei ou a decisão judicial, com ligação.
- **Os pontos controvertidos são opções**, e o resultado inclui uma nota. As predefinições seguem a jurisprudência consolidada do tribunal superior; na falta dela, a data mais cedo.
- **Não adivinha.** Datas fora dos dados verificados dão um erro em vez de um dia errado.
- **Verificado de vários lados.**
  - 331 casos de teste escritos à mão, muitos retirados de decisões judiciais e de exemplos oficiais.
  - Python e TypeScript têm de coincidir em 1800 casos aleatórios.
  - Os calendários são comparados com dados independentes.
  - Antes da publicação, cada regra foi verificada nas suas fontes ([relatório](docs/verification.md)).

## Em 12 línguas, em qualquer ecrã

<p align="center">
  <img width="30%" alt="Resultado no telemóvel em inglês: um prazo federal dos EUA com três dias acrescentados por notificação postal." src="docs/images/phone-en.png">
  <img width="30%" alt="Resultado no telemóvel em árabe, da direita para a esquerda." src="docs/images/phone-ar.png">
  <img width="30%" alt="Resultado no telemóvel em japonês com o tema escuro: um prazo de recurso alemão com o calendário de Munique." src="docs/images/phone-ja.png">
</p>

## Contribuir

As correções e revisões feitas por juristas são as contribuições mais valiosas. Se um resultado estiver errado, abra uma [correção de regra](https://github.com/DoGood-Studio/legal-deadline-calculator/issues/new?template=rule-correction.yml) com a fonte. Uma nova jurisdição é um pacote de regras JSON com casos de teste; veja [CONTRIBUTING.md](CONTRIBUTING.md) e [docs/rulepacks.md](docs/rulepacks.md).

---

<sub>O lexdays é uma ferramenta informativa e não constitui aconselhamento jurídico. Prevalecem a lei, a jurisprudência, as decisões judiciais e a prática local; verifique sempre um prazo importante. [Licença MIT](LICENSE).</sub>

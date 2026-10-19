# Writing a rule pack

A rule pack describes how one jurisdiction computes a deadline. It is a JSON file in `data/rulepacks/<country>/<name>.json`, validated by [`spec/rulepack.schema.json`](../spec/rulepack.schema.json). The engine checks the same rules when it loads the pack and rejects unknown fields, so typos fail loudly.

## Shape

```jsonc
{
  "$schema": "../../../spec/rulepack.schema.json",
  "id": "xx/court",                       // must match the file path
  "name": { "en": "...", "tr": "..." },
  "jurisdiction": "XX",
  "calendar": "xx",                       // default holiday calendar
  "calendar_family": "xx",                // optional: allow calendar="xx-region" overrides
  "status": "beta",
  "description": { "en": "..." },
  "disclaimer": { "en": "Informational tool, not legal advice. ..." },
  "non_working": { "weekend": true, "kinds": ["public"], "half_days": "working" },
  "options": { ... },
  "citations": { ... },
  "steps": [ ... ]
}
```

## Steps

The engine runs the steps in order. A step whose `when` condition is false is skipped. **Exactly one `count` step must apply** to any computation; anything else is a data error.

| Step | What it does | Main fields |
|---|---|---|
| `shift_trigger` | Moves the start date before counting (deemed service, publication + N days). Must come before `count`. | `days` |
| `recess` with `mode: "defer_start"` | If the start date falls in a recess, counting starts after it. Must come before `count`. | `name`, `periods` |
| `count` | Counts the period: days (excluding the start day by default), weeks (same weekday), months and years (same date, clamped to the month end) or business days. | `exclude_start_day`, `clear_days`, `business_days` |
| `recess` with `mode: "extend"` | If the current date falls in a recess, the period ends `extension_days` after the recess, counted from its last day (`count_from: "end"`) or from the day after (`"day_after_end"`). | `periods`, `extension_days`, `count_from` |
| `recess` with `mode: "suspend"` | Recess days inside the period are not counted. | `periods` |
| `roll` | Moves a non-working day to the next working day, or the previous one when counting backwards (`direction: "auto"`). | `direction`, `kinds`, `half_days`, `weekend` |
| `add_days` | Adds calendar days after counting (e.g. FRCP 6(d)'s 3 days for mail). | `days` |
| `ends_at` | Records the time the last day ends. | `time` (`HH:MM`) |
| `notice` | Attaches a caveat to the result. | `code`, `text` |

Every step can have `when`, `cite` (a key of `citations`), `message` (replacement template) and `messages` (replacement template per message key, e.g. only for `roll.forward`).

Recess `periods` are month-day windows (`{"start": "07-20", "end": "08-31"}`). They may cross the new year and may have `since`/`until` years.

## Conditions

A `when` object holds if **all** of its keys hold:

| Key | True when |
|---|---|
| `option` + `equals` / `in` | the option has that value |
| `unit`, `unit_in` | the period unit matches |
| `min_amount`, `max_amount` | the period amount is in range |
| `direction` | counting `"after"` or `"before"` the trigger |
| `trigger_from`, `trigger_before` | the trigger date is on/after, or before, an ISO date (for law changes) |
| `trigger_within` | the date counting starts from (e.g. the deemed date of service) falls in one of the month-day windows |
| `date_within` | the current date falls in one of the windows |
| `date_from`, `date_before` | the current date (in a notice, the deadline) is on/after, or before, an ISO date (for dated events such as an extraordinary suspension of periods) |
| `day_has` | the current date has a half-day holiday (`"half_day"`) or a holiday of the given kind (e.g. `"administrative"`) |
| `non_working_day` | the current date is (`true`) or is not (`false`) a non-working day |
| `applied` | an earlier step of this type (e.g. `"recess"`) changed the date |
| `all`, `any`, `not` | combinations |

Conditions are validated at load time: testing an option value that the option can never take is an error.

## Options

```json
"options": {
  "filing": {
    "values": ["electronic", "physical"],
    "default": "electronic",
    "description": { "en": "Electronic filing ends at 23:59 ..." }
  }
}
```

Callers pass options as `compute(..., options={"filing": "physical"})`. Unknown options and invalid values raise `OptionError`. A step field can take its value from an option with `{"$option": "name"}`, e.g. `"count_from": {"$option": "recess_extension_from"}`.

**Disputed points.** When courts or practitioners disagree, add an option and a `notice` that explains the disagreement whenever it matters (the `applied` condition helps: notify only when the disputed step changed the date). The default follows settled high-court case law; where there is none, it is the **earlier, safer** date. Never silently choose one reading.

## Citations

```json
"citations": {
  "hmk_93": {
    "label": { "en": "HMK Art. 93", "tr": "HMK m.93" },
    "url": "https://www.mevzuat.gov.tr/MevzuatMetin/1.5.6100.pdf",
    "quote": { "tr": "Resmî tatil günleri, süreye dâhildir. ..." }
  }
}
```

Statute texts are generally not protected by copyright. Quote them verbatim and keep decision quotes short.

## Messages

Default explanation templates live in [`data/i18n/messages.json`](../data/i18n/messages.json) and are shared by both implementations. Placeholders such as `{from}`, `{to}`, `{n}`, `{days}`, `{recess}`, `{reason}` and `{time}` are filled in per step. A test checks that no placeholder is left unfilled in any language.

## Test vectors

Add cases to `vectors/<country>/deadline.json`:

```json
{ "id": "hmk-v09-recess-8-september-saturday", "pack": "tr/hmk",
  "trigger": "2018-08-08", "period": "P2W",
  "expect": { "deadline": "2018-09-10", "notices": [] },
  "source": "Yargıtay 2. HD E.2019/2507 K.2019/8376" }
```

Optional fields are `direction`, `options` and `calendar`. Under `expect` you can also check `steps`, `changed`, `ends_at` and `notices`. Both test-suites pick the file up automatically.

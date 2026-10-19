# lexdays

**Legal deadlines and business days you can verify.** lexdays computes the last day to act and explains every step, with the statute or court decision it comes from.

- Türkiye (HMK, İİK, CMK, İYUK, VUK, Constitutional Court), US federal courts (FRCP 6), England and Wales (CPR 2.8), the EU Court of Justice and Germany (ZPO)
- Judicial recesses, half-day holidays, deemed service, add-on days for mail, counting back from a hearing, clear days, month ends
- Calculation steps explained in 12 languages
- Disputed points are options with a notice; dates outside the verified holiday data throw instead of guessing
- No dependencies, MIT licensed, typed, ESM and CommonJS; the Python package (`pip install lexdays`) gives identical results

```bash
npm install lexdays
```

```ts
import { compute, calendar } from "lexdays";

const r = compute("tr/hmk", "2026-07-30", "P2W");   // Turkish civil procedure, 2 weeks from service
r.deadline;                                         // "2026-09-08": extended by the judicial recess
r.explain("en");                                    // numbered steps, each with its citation

compute("us/frcp", "2025-07-31", "P30D", { options: { service: "mail" } }).deadline;   // "2025-09-05"
compute("gb-eaw/cpr", "2025-10-20", "P3D", { direction: "before" }).deadline;          // "2025-10-14"
compute("de/zpo", "2025-07-15", "P1M", { calendar: "de-by-catholic" }).deadline;       // "2025-08-18"

calendar("tr").addBusinessDays("2026-05-22", 3);   // "2026-06-01": skips the Feast of Sacrifice
```

Dates are plain `YYYY-MM-DD` strings. JavaScript `Date` objects are rejected on purpose, because which calendar day a moment belongs to depends on a time zone.

Documentation, rule sources and the live demo: <https://github.com/DoGood-Studio/lexdays>

This is an informational tool, not legal advice. Always check a deadline that matters.

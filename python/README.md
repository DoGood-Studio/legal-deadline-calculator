# lexdays

**Legal deadlines and business days you can verify.** lexdays computes the last day to act and explains every step, with the statute or court decision it comes from.

- Türkiye (HMK, İİK, CMK, İYUK, VUK, Constitutional Court), US federal courts (FRCP 6), England and Wales (CPR 2.8), the EU Court of Justice and Germany (ZPO)
- Judicial recesses, half-day holidays, deemed service, add-on days for mail, counting back from a hearing, clear days, month ends
- Calculation steps explained in 12 languages
- Disputed points are options with a notice; dates outside the verified holiday data raise an error instead of guessing
- No dependencies, MIT licensed; the TypeScript package (`npm install lexdays`) gives identical results

```bash
pip install lexdays
```

```python
import lexdays

r = lexdays.compute("tr/hmk", "2026-07-30", "P2W")   # Turkish civil procedure, 2 weeks from service
r.deadline                                          # datetime.date(2026, 9, 8): extended by the judicial recess
print(r.explain("en"))                              # numbered steps, each with its citation

lexdays.compute("us/frcp", "2025-07-31", "P30D", options={"service": "mail"}).deadline
# datetime.date(2025, 9, 5)

lexdays.compute("gb-eaw/cpr", "2025-10-20", "P3D", direction="before").deadline
# datetime.date(2025, 10, 14): 3 clear days before the hearing

lexdays.compute("de/zpo", "2025-07-15", "P1M", calendar="de-by-catholic").deadline
# datetime.date(2025, 8, 18): 15 August is a holiday at a Munich court

lexdays.calendar("tr").add_business_days("2026-05-22", 3)
# datetime.date(2026, 6, 1): skips the Feast of Sacrifice
```

Command line:

```bash
lexdays deadline tr/hmk 2026-07-30 P2W --lang de
lexdays deadline de/zpo 2025-07-25 P2W --calendar de-by-augsburg
lexdays holidays tr 2026
```

Documentation, rule sources and the live demo: <https://github.com/DoGood-Studio/legal-deadline-calculator>

This is an informational tool, not legal advice. Always check a deadline that matters.

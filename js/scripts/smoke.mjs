// Runs the built ESM bundle on the oldest supported Node versions (no dev toolchain needed).
import assert from "node:assert/strict";
import { calendar, compute } from "../dist/index.js";

assert.equal(compute("tr/hmk", "2026-07-30", "P2W").deadline, "2026-09-08");
assert.equal(compute("us/frcp", "2025-07-31", "P30D", { options: { service: "mail" } }).deadline, "2025-09-05");
assert.equal(calendar("gb-eaw").addBusinessDays("2025-12-24", 1), "2025-12-29");
console.log(`ESM bundle OK on Node ${process.version}`);

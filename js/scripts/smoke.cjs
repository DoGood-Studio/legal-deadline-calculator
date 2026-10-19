// Runs the built CommonJS bundle on the oldest supported Node versions.
const assert = require("node:assert/strict");
const { compute } = require("../dist/index.cjs");

assert.equal(compute("de/zpo", "2025-07-15", "P1M", { calendar: "de-by-catholic" }).deadline, "2025-08-18");
console.log(`CJS bundle OK on Node ${process.version}`);

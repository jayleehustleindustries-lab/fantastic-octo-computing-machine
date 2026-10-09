import { describe, expect, it } from "vitest";
import {
  ACTIVITY_LEVELS,
  basalMetabolicRate,
  macroCalories,
  PROGRAM_WEEKS,
  remapNumbers,
  totalDailyEnergy,
  type BodyStats,
} from "./remap";
import { programProblems } from "./remapProgram";

const man: BodyStats = { sex: "male", age: 35, heightCm: 180, weightKg: 90, activity: "moderate", goal: "fat-loss" };

describe("basalMetabolicRate (Mifflin-St Jeor)", () => {
  it("matches the published formula for men and women", () => {
    // 10*90 + 6.25*180 - 5*35 + 5 = 1855
    expect(basalMetabolicRate(man)).toBe(1855);
    // 10*65 + 6.25*165 - 5*28 - 161 = 1380.25
    expect(basalMetabolicRate({ sex: "female", age: 28, heightCm: 165, weightKg: 65 })).toBeCloseTo(1380.25);
  });

  it("uses the midpoint when sex isn't given", () => {
    const m = basalMetabolicRate({ ...man, sex: "male" });
    const f = basalMetabolicRate({ ...man, sex: "female" });
    expect(basalMetabolicRate({ ...man, sex: "unspecified" })).toBe((m + f) / 2);
  });
});

describe("totalDailyEnergy", () => {
  it("multiplies BMR by the activity factor", () => {
    for (const [level, { factor }] of Object.entries(ACTIVITY_LEVELS)) {
      expect(totalDailyEnergy({ ...man, activity: level as BodyStats["activity"] })).toBeCloseTo(1855 * factor);
    }
    expect(ACTIVITY_LEVELS.sedentary.factor).toBe(1.2);
    expect(ACTIVITY_LEVELS.athlete.factor).toBe(1.9);
  });
});

describe("remapNumbers", () => {
  it("sets a 20% deficit for fat loss and reconciles macros to the target", () => {
    const n = remapNumbers(man);
    expect(n.bmr).toBe(1855);
    expect(n.tdee).toBe(Math.round(1855 * 1.55)); // 2875
    expect(n.targetCalories).toBe(2300); // 2875 * 0.8 = 2300.2
    expect(n.proteinG).toBe(180); // 0.9 g/lb of 198.4 lb
    expect(n.fatG).toBe(65); // max(0.3 g/lb = 60, 25% of kcal = 64) → 65
    expect(Math.abs(macroCalories(n) - n.targetCalories)).toBeLessThanOrEqual(20);
  });

  it("applies goal multipliers", () => {
    const tdee = remapNumbers({ ...man, goal: "performance" }).targetCalories;
    expect(remapNumbers({ ...man, goal: "muscle-gain" }).targetCalories).toBeGreaterThan(tdee);
    expect(remapNumbers({ ...man, goal: "recomp" }).targetCalories).toBeLessThan(tdee);
  });

  it("never goes below BMR or the safety floor", () => {
    const small = remapNumbers({ sex: "female", age: 60, heightCm: 150, weightKg: 48, activity: "sedentary", goal: "fat-loss" });
    expect(small.floorApplied).toBe(true);
    expect(small.targetCalories).toBeGreaterThanOrEqual(1200);
    expect(small.targetCalories).toBeGreaterThanOrEqual(small.bmr - 5);
    expect(small.carbsG).toBeGreaterThanOrEqual(50);
  });

  it("bases protein on goal weight when BMI is 30 or more", () => {
    const heavy = remapNumbers({ ...man, weightKg: 130, goalWeightKg: 95 });
    expect(heavy.bmi).toBeGreaterThanOrEqual(30);
    expect(heavy.proteinG).toBe(190); // 0.9 g/lb of 209.4 lb (95 kg), not 258 lb
    const lean = remapNumbers({ ...man, goalWeightKg: 80 });
    expect(lean.proteinG).toBe(180); // BMI < 30: current weight
  });
});

describe("PROGRAM_WEEKS", () => {
  it("follows Coach Jay's lengths by level", () => {
    expect(PROGRAM_WEEKS.beginner).toEqual({ min: 8, max: 12 });
    expect(PROGRAM_WEEKS.intermediate).toEqual({ min: 6, max: 8 });
    expect(PROGRAM_WEEKS.advanced.max).toBeLessThanOrEqual(6);
  });
});

describe("programProblems", () => {
  const day = { label: "Day 1", title: "A", focus: "B", finisher: "", exercises: [] };
  const base = {
    title: "", summary: "", lengthRationale: "", warmup: "", deload: "", cardioAndSteps: "",
    nutrition: { summary: "", priorities: [], proteinTips: [], timing: "", adjustments: "" },
    habits: [], checkIns: "", safety: [],
  };

  it("accepts phases that cover every week with the right day count", () => {
    const p = { ...base, weeks: 8, phases: [
      { name: "A", startWeek: 1, endWeek: 4, goal: "", days: [day, day, day], progression: "" },
      { name: "B", startWeek: 5, endWeek: 8, goal: "", days: [day, day, day], progression: "" },
    ] };
    expect(programProblems(p, { min: 8, max: 12 }, 3)).toEqual([]);
  });

  it("flags length, gaps and day-count mismatches", () => {
    const p = { ...base, weeks: 6, phases: [
      { name: "A", startWeek: 1, endWeek: 2, goal: "", days: [day, day], progression: "" },
      { name: "B", startWeek: 4, endWeek: 6, goal: "", days: [day, day, day], progression: "" },
    ] };
    const problems = programProblems(p, { min: 8, max: 12 }, 3);
    expect(problems.join(" ")).toMatch(/must be 8-12 weeks/);
    expect(problems.join(" ")).toMatch(/no gaps or overlaps/);
    expect(problems.join(" ")).toMatch(/"A" has 2 training days/);
  });
});

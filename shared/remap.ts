/**
 * Remap numbers. These are computed here, not by the model, so they are exact,
 * testable, and identical on the intake page and in the delivered program.
 */

export type Sex = "male" | "female" | "unspecified";
export type Goal = "fat-loss" | "recomp" | "muscle-gain" | "performance";
export type Experience = "beginner" | "intermediate" | "advanced";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "very" | "athlete";

export const ACTIVITY_LEVELS: Record<ActivityLevel, { factor: number; label: string; detail: string }> = {
  sedentary: { factor: 1.2, label: "Sedentary", detail: "Desk job, under ~5,000 steps a day, little exercise" },
  light: { factor: 1.375, label: "Lightly active", detail: "Light exercise 1–3 days a week or on your feet some of the day" },
  moderate: { factor: 1.55, label: "Moderately active", detail: "Training 3–5 days a week, ~7,000–10,000 steps" },
  very: { factor: 1.725, label: "Very active", detail: "Hard training 6–7 days a week or a physical job" },
  athlete: { factor: 1.9, label: "Athlete", detail: "Physical job plus hard daily training, or twice-a-day sessions" },
};

export const GOALS: Record<Goal, { multiplier: number; label: string }> = {
  "fat-loss": { multiplier: 0.8, label: "Lose fat" },
  recomp: { multiplier: 0.9, label: "Recomp (lose fat, build muscle)" },
  "muscle-gain": { multiplier: 1.1, label: "Build muscle" },
  performance: { multiplier: 1.0, label: "Performance / maintain" },
};

/** Program length bounds in weeks, by training experience. */
export const PROGRAM_WEEKS: Record<Experience, { min: number; max: number }> = {
  beginner: { min: 8, max: 12 },
  intermediate: { min: 6, max: 8 },
  advanced: { min: 4, max: 6 },
};

export type BodyStats = {
  sex: Sex;
  age: number;
  heightCm: number;
  weightKg: number;
  goalWeightKg?: number;
  activity: ActivityLevel;
  goal: Goal;
};

export type RemapNumbers = {
  bmr: number;
  activityFactor: number;
  tdee: number;
  targetCalories: number;
  proteinG: number;
  fatG: number;
  carbsG: number;
  bmi: number;
  floorApplied: boolean;
};

const KG_PER_LB = 0.45359237;
export const lbToKg = (lb: number) => lb * KG_PER_LB;
export const kgToLb = (kg: number) => kg / KG_PER_LB;
export const inchesToCm = (inches: number) => inches * 2.54;

/** Mifflin-St Jeor resting energy expenditure, kcal/day. */
export function basalMetabolicRate({ sex, age, heightCm, weightKg }: Pick<BodyStats, "sex" | "age" | "heightCm" | "weightKg">): number {
  const base = 10 * weightKg + 6.25 * heightCm - 5 * age;
  const offset = sex === "male" ? 5 : sex === "female" ? -161 : -78; // unspecified: midpoint of the two
  return base + offset;
}

export function totalDailyEnergy(stats: Pick<BodyStats, "sex" | "age" | "heightCm" | "weightKg" | "activity">): number {
  return basalMetabolicRate(stats) * ACTIVITY_LEVELS[stats.activity].factor;
}

/** Calorie and macro targets for a Remap, rounded the way a coach would write them. */
export function remapNumbers(stats: BodyStats): RemapNumbers {
  const bmr = basalMetabolicRate(stats);
  const activityFactor = ACTIVITY_LEVELS[stats.activity].factor;
  const tdee = bmr * activityFactor;

  const raw = tdee * GOALS[stats.goal].multiplier;
  const sexFloor = stats.sex === "male" ? 1500 : 1200;
  const floor = Math.max(bmr, sexFloor);
  const floorApplied = raw < floor;
  const targetCalories = roundTo(Math.max(raw, floor), 10);

  const bmi = stats.weightKg / (stats.heightCm / 100) ** 2;
  // In higher body-fat ranges, base protein on the goal weight so the target stays realistic.
  const referenceKg = bmi >= 30 && stats.goalWeightKg ? Math.min(stats.goalWeightKg, stats.weightKg) : stats.weightKg;
  const referenceLb = kgToLb(referenceKg);

  const proteinG = roundTo(0.9 * referenceLb, 5);
  const fatG = roundTo(Math.max(0.3 * referenceLb, (0.25 * targetCalories) / 9), 5);
  const carbsG = Math.max(50, roundTo((targetCalories - proteinG * 4 - fatG * 9) / 4, 5));

  return {
    bmr: Math.round(bmr),
    activityFactor,
    tdee: Math.round(tdee),
    targetCalories,
    proteinG,
    fatG,
    carbsG,
    bmi: Math.round(bmi * 10) / 10,
    floorApplied,
  };
}

/** Calories implied by the macro targets (4/4/9), which can differ slightly from the target after rounding. */
export const macroCalories = (n: Pick<RemapNumbers, "proteinG" | "fatG" | "carbsG">) => n.proteinG * 4 + n.carbsG * 4 + n.fatG * 9;

function roundTo(value: number, step: number) {
  return Math.round(value / step) * step;
}

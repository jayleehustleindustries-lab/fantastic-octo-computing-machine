import { z } from "zod";

/**
 * The shape of a delivered Remap program. Claude fills it through structured
 * outputs; the page renders it; Airtable stores it as JSON. The calorie and
 * macro numbers are not in here: they come from shared/remap.ts.
 */

export const remapExercise = z.object({
  name: z.string(),
  sets: z.string().describe('e.g. "4"'),
  reps: z.string().describe('e.g. "6-8" or "30s"'),
  rest: z.string().describe('e.g. "2 min"'),
  effort: z.string().describe('Target effort, e.g. "RPE 7-8" or "2 reps in reserve"'),
  notes: z.string().describe("One coaching cue or substitution"),
});

export const remapDay = z.object({
  label: z.string().describe('e.g. "Day 1"'),
  title: z.string().describe('e.g. "Upper — Push"'),
  focus: z.string(),
  exercises: z.array(remapExercise),
  finisher: z.string().describe('Optional conditioning or core finisher, or "" if none'),
});

export const remapPhase = z.object({
  name: z.string().describe('e.g. "Phase 1 — Foundation"'),
  startWeek: z.number().int(),
  endWeek: z.number().int(),
  goal: z.string(),
  days: z.array(remapDay).describe("One entry per training day in the week"),
  progression: z.string().describe("Exactly how to progress week to week inside this phase"),
});

export const remapProgram = z.object({
  title: z.string(),
  summary: z.string().describe("2-3 sentences, written to the client"),
  weeks: z.number().int(),
  lengthRationale: z.string().describe("Why this length for this person"),
  phases: z.array(remapPhase),
  warmup: z.string(),
  deload: z.string(),
  cardioAndSteps: z.string(),
  nutrition: z.object({
    summary: z.string().describe("How to use the calorie and macro targets"),
    priorities: z.array(z.string()).describe("What to eat more of and build meals around; not a meal plan"),
    proteinTips: z.array(z.string()),
    timing: z.string(),
    adjustments: z.string().describe("When and how to adjust intake based on weekly weigh-ins"),
  }),
  habits: z.array(z.string()),
  checkIns: z.string().describe("What to track each week and how to judge progress"),
  safety: z.array(z.string()),
});

export type RemapProgram = z.infer<typeof remapProgram>;

/** Checks the parts of a program that a schema can't express. Returns problems, or [] if it's sound. */
export function programProblems(program: RemapProgram, bounds: { min: number; max: number }, daysPerWeek: number): string[] {
  const problems: string[] = [];
  if (program.weeks < bounds.min || program.weeks > bounds.max) {
    problems.push(`The program must be ${bounds.min}-${bounds.max} weeks for this level; it is ${program.weeks}.`);
  }
  let expectedStart = 1;
  for (const phase of [...program.phases].sort((a, b) => a.startWeek - b.startWeek)) {
    if (phase.startWeek !== expectedStart || phase.endWeek < phase.startWeek) {
      problems.push(`Phases must cover weeks 1-${program.weeks} in order with no gaps or overlaps.`);
      break;
    }
    expectedStart = phase.endWeek + 1;
    if (phase.days.length !== daysPerWeek) {
      problems.push(`"${phase.name}" has ${phase.days.length} training days; the client trains ${daysPerWeek} days a week.`);
    }
  }
  if (program.phases.length && expectedStart !== program.weeks + 1) {
    problems.push(`Phases must end at week ${program.weeks}.`);
  }
  if (!program.phases.length) problems.push("The program has no phases.");
  return Array.from(new Set(problems));
}

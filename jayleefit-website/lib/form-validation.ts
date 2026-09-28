import { z } from "zod";

// Empty inputs arrive as "" from the form, which `.optional()` alone rejects
// for a min-length rule — so blank optional fields must be allowed explicitly.
const optionalText = z.string().trim().optional().or(z.literal(""));

export const IntakeFormSchema = z.object({
  name: z.string().trim().min(2, "Name must be at least 2 characters"),
  email: z.string().trim().email("Please enter a valid email address"),
  phone: z
    .string()
    .trim()
    .min(10, "Please enter a valid phone number")
    .optional()
    .or(z.literal("")),
  goals: z
    .array(z.string(), { error: "Please select at least one goal" })
    .min(1, "Please select at least one goal"),
  weight: optionalText,
  timezone: optionalText,
  budget: optionalText,
  notes: optionalText,
});

export type IntakeFormData = z.infer<typeof IntakeFormSchema>;

import { NextRequest, NextResponse } from "next/server";
import { z } from "zod";
import { submitIntakeToAirtable } from "@/lib/airtable";
import { IntakeFormSchema } from "@/lib/form-validation";

export async function POST(request: NextRequest) {
  const body = await request.json().catch(() => null);
  const parsed = IntakeFormSchema.safeParse(body);

  if (!parsed.success) {
    return NextResponse.json(
      { success: false, message: z.prettifyError(parsed.error) },
      { status: 400 }
    );
  }

  try {
    const record = await submitIntakeToAirtable(parsed.data);
    return NextResponse.json(
      { success: true, message: "Intake submitted successfully", recordId: record.id },
      { status: 201 }
    );
  } catch (error) {
    // Server-side detail (missing token, Airtable errors) goes to the logs,
    // not to the person filling in the form.
    console.error("Intake submission error:", error);
    return NextResponse.json(
      {
        success: false,
        message:
          "We couldn't save your intake just now. Please try again, or email jayleehustle.industries@gmail.com.",
      },
      { status: 500 }
    );
  }
}

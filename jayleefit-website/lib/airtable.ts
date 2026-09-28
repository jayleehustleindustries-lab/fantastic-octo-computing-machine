import { IntakeFormData } from "./form-validation";

const AIRTABLE_API_URL = "https://api.airtable.com/v0";

/**
 * Website intakes are leads, not clients: they land in Lead Pipeline and get
 * linked to a Clients record only once they convert. Every field written here
 * is plain text or a date, so no select option can reject a submission.
 */
export async function submitIntakeToAirtable(data: IntakeFormData) {
  const token = process.env.AIRTABLE_API_TOKEN;
  const baseId = process.env.AIRTABLE_BASE_ID;
  const tableName = process.env.AIRTABLE_LEADS_TABLE || "Lead Pipeline";

  if (!token || !baseId) {
    throw new Error("Missing Airtable configuration");
  }

  const details = [
    `Goals: ${data.goals.join(", ")}`,
    data.phone && `Phone: ${data.phone}`,
    data.weight && `Current weight: ${data.weight}`,
    data.timezone && `Timezone: ${data.timezone}`,
    data.budget && `Budget: ${data.budget}`,
    data.notes && `Notes: ${data.notes}`,
  ].filter(Boolean);

  const fields: Record<string, unknown> = {
    "Lead Name": data.name,
    Email: data.email,
    Source: "jayleefit.com intake form",
    "Created Date": new Date().toISOString().slice(0, 10),
    "Funnel Stage": "Intake Received",
    Notes: details.join("\n"),
  };

  const response = await fetch(
    `${AIRTABLE_API_URL}/${baseId}/${encodeURIComponent(tableName)}`,
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ records: [{ fields }] }),
    }
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(
      error.error?.message || `Airtable responded ${response.status}`
    );
  }

  const result = await response.json();
  return result.records[0];
}

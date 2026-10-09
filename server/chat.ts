import { z } from "zod";
import type {
  BetaContentBlockParam,
  BetaMessageParam,
  BetaTool,
  BetaToolResultBlockParam,
} from "@anthropic-ai/sdk/resources/beta/messages/messages";
import type { ChatLead } from "./airtable";
import { ASK_JAY_SYSTEM_PROMPT } from "./chatPrompt";
import { CLAUDE_MODEL, claudeConfigured, getClaude } from "./claude";

/**
 * Ask Jay: one visitor turn in, one reply out. The browser keeps the
 * conversation and sends it back as plain text each turn, so the server stores
 * nothing and a visitor can't inject a system prompt or tool results.
 */

const MAX_HISTORY = 20;
const MAX_TOOL_ROUNDS = 3;

export const chatInput = z.object({
  messages: z
    .array(z.object({
      role: z.enum(["user", "assistant"]),
      content: z.string().trim().min(1).max(2000),
    }))
    .min(1)
    .max(30)
    .refine(
      messages => messages.every((m, i) => m.role === (i % 2 === 0 ? "user" : "assistant")),
      "Messages must alternate, starting with the visitor.",
    )
    .refine(messages => messages[messages.length - 1].role === "user", "The last message must be the visitor's."),
});

export type ChatHistory = z.infer<typeof chatInput>["messages"];

const leadInput = z.object({
  name: z.string().trim().min(1).max(120),
  email: z.string().trim().email().max(200),
  goal: z.string().trim().max(500).default(""),
  summary: z.string().trim().max(1500).default(""),
  ready_to_apply: z.boolean().default(false),
});

export const SAVE_LEAD_TOOL: BetaTool = {
  name: "save_lead",
  description:
    "Pass a visitor's details to Coach Jay as a lead. Call only after the visitor has given their name and email and said yes to passing them on.",
  strict: true,
  input_schema: {
    type: "object",
    properties: {
      name: { type: "string", description: "The visitor's name as they gave it." },
      email: { type: "string", description: "The email address the visitor typed." },
      goal: { type: "string", description: "Their main goal, in their words." },
      summary: { type: "string", description: "Two or three sentences for Coach Jay: goal, situation, schedule, anything notable." },
      ready_to_apply: { type: "boolean", description: "True if they want to start the application now." },
    },
    required: ["name", "email", "goal", "summary", "ready_to_apply"],
    additionalProperties: false,
  },
};

export type SaveLead = (lead: ChatLead) => Promise<void>;

export type ChatResult = { reply: string; lead?: { name: string; email: string } };

const REFUSAL_REPLY =
  "I can't help with that one. I'm here for questions about JayLee Fit coaching, starting plans, and applying. What are you working toward?";

export async function askJay(history: ChatHistory, saveLead: SaveLead): Promise<ChatResult> {
  if (!claudeConfigured()) throw new Error("Ask Jay is not switched on yet.");

  // Keep the most recent turns, starting on a visitor message.
  let recent = history.slice(-MAX_HISTORY);
  if (recent[0].role !== "user") recent = recent.slice(1);
  const messages: BetaMessageParam[] = recent.map(m => ({ role: m.role, content: m.content }));

  let lead: ChatResult["lead"];

  for (let round = 0; round < MAX_TOOL_ROUNDS; round++) {
    const response = await getClaude().beta.messages.create({
      model: CLAUDE_MODEL,
      // Thinking shares this budget, so leave room beyond a ~500-word plan.
      max_tokens: 8000,
      output_config: { effort: "low" },
      // On a safety decline, the API reruns the request on a fallback model.
      betas: ["server-side-fallback-2026-07-01"],
      fallbacks: "default",
      cache_control: { type: "ephemeral" },
      system: ASK_JAY_SYSTEM_PROMPT,
      tools: [SAVE_LEAD_TOOL],
      tool_choice: { type: "auto" },
      messages,
    });

    if (response.stop_reason === "refusal") return { reply: REFUSAL_REPLY, lead };

    const toolUses = response.content.flatMap(block => (block.type === "tool_use" ? [block] : []));
    if (response.stop_reason !== "tool_use" || toolUses.length === 0) {
      const reply = response.content
        .flatMap(block => (block.type === "text" ? [block.text] : []))
        .join("")
        .trim();
      return { reply: reply || "Sorry, I lost my train of thought. Could you say that again?", lead };
    }

    // Run the tool calls, then send the results back in one message.
    messages.push({ role: "assistant", content: response.content as BetaContentBlockParam[] });
    const results: BetaToolResultBlockParam[] = [];
    for (const use of toolUses) {
      if (use.name !== SAVE_LEAD_TOOL.name) {
        results.push({ type: "tool_result", tool_use_id: use.id, is_error: true, content: "Unknown tool." });
        continue;
      }
      const parsed = leadInput.safeParse(use.input);
      if (!parsed.success) {
        results.push({ type: "tool_result", tool_use_id: use.id, is_error: true, content: "That email or name doesn't look right. Ask the visitor to check it." });
        continue;
      }
      try {
        const { ready_to_apply, ...rest } = parsed.data;
        await saveLead({ ...rest, readyToApply: ready_to_apply });
        lead = { name: rest.name, email: rest.email };
        results.push({ type: "tool_result", tool_use_id: use.id, content: "Saved. The Continue my application button is now showing below the chat." });
      } catch (error) {
        // Keep storage errors out of the conversation; the visitor only needs the way forward.
        console.error("[Ask Jay] save_lead failed:", error);
        results.push({
          type: "tool_result",
          tool_use_id: use.id,
          is_error: true,
          content: "Couldn't save the details right now. Point them to the Apply section on the page.",
        });
      }
    }
    messages.push({ role: "user", content: results });
  }

  return { reply: "Got it. Use the Apply section on this page to finish up, and Coach Jay will take it from there.", lead };
}

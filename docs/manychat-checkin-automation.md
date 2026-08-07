# ManyChat — client check-in automation (JayLeeFit)

**Scope: JayLeeFit coaching only.** Nothing here touches the EHC resale
side in `storefront/`. Different business, different data, different
schedule — don't wire them together.

## What I could and couldn't do

There is no ManyChat connector available to me, so I can't log into your
account and build the flow. Everything below is the exact build — objects
to create, trigger config, and the message copy — for you to enter in
ManyChat's UI. The Airtable half is specified against your real schema.

## The constraint that shapes the whole design

Two hard limits, neither of which is a preference:

1. **Instagram's 24-hour messaging window.** Meta blocks a business from
   DMing anyone who hasn't messaged it in the last 24 hours. A scheduled
   "time for your check-in" DM to a client who hasn't just messaged you
   is exactly what this prevents. It applies on *every* ManyChat tier.
2. **Free tier has no External Request action.** A free flow can't POST
   to Airtable, so collected answers can't write themselves back.

So ManyChat cannot be the thing that *starts* the check-in. What it's
genuinely good at is handling the conversation once the client replies —
and that's worth having, because it's the part that takes your time.

**The working shape:**

```
You post an IG Story: "Weekly check-in — reply CHECKIN"
        │
        ▼
Client replies  ──►  opens the 24h window (this is what makes it legal)
        │
        ▼
ManyChat runs the check-in Q&A automatically
        │
        ▼
Answers stored in ManyChat User Fields
        │
        ▼
Export CSV  ──►  import into Airtable   (manual on Free; automatic on Pro)
```

The prompt goes out through a channel that's allowed (a Story, an email,
or Telegram later). The client's reply is what opens the door. ManyChat
then does the repetitive part without you typing anything.

## Step 1 — Airtable: add the join key

Your `Clients` table (`tbl9fkgO75F5FDfiw`) has `Telegram Chat ID` but no
Instagram equivalent, so an exported ManyChat row can't be matched to a
client record. Add one field:

| Field | Type | Purpose |
|---|---|---|
| `ManyChat Subscriber ID` | Single line text | Join key between a ManyChat export row and a client record |

Also record each client's Instagram handle if you don't already — the
subscriber ID is the reliable key, the handle is the human-readable one.

## Step 2 — ManyChat: Custom User Fields

Settings → Fields → **User Fields**. Create these (names matter, they
become your CSV column headers):

| Field name | Type | Maps to Airtable |
|---|---|---|
| `checkin_weight` | Number | `Progress Tracking` → `Weight (kg)` |
| `checkin_energy` | Number | `Progress Tracking` → `Energy Level` |
| `checkin_mood` | Number | `Progress Tracking` → `Mood` |
| `checkin_adherence` | Number | `Check-ins` → `Check-in Notes` |
| `checkin_wins` | Text | `Check-ins` → `Client Self-Reported Updates` |
| `checkin_struggles` | Text | `Check-ins` → `Client Self-Reported Updates` |
| `checkin_date` | Date | `Check-ins` → `Scheduled Date` |

`Mood` and `Energy Level` are single-selects in Airtable — when you
import, map the 1-5 numbers onto whatever choices those fields already
have rather than inventing new ones.

## Step 3 — ManyChat: Tag

Create one tag: **`checkin-completed`**. Applied at the end of the flow.
It's how you see at a glance who has and hasn't checked in this week,
without reading any conversations.

## Step 4 — ManyChat: the trigger

Automation → New Automation → Trigger: **Instagram → Keyword**.

Keywords: `CHECKIN`, `CHECK IN`, `CHECK-IN` (add all three; people type
what they type).

Match type: **contains**, so "checkin done!" still fires.

## Step 5 — the flow

Each step is a ManyChat *Question* block saving to the field named. Keep
the voice yours — this is a coach talking, not a form.

**1 — Open**
> Weekly check-in time. Six quick questions, takes about a minute.
> Answer as honestly as you can — the useful data is the honest data,
> not the flattering data.

**2 — Weight** → save to `checkin_weight` (Number)
> Current weight? Just the number.

**3 — Adherence** → save to `checkin_adherence` (Number, 1-10)
> How closely did you stick to the plan this week? 1-10.
> A 6 I know about is worth more to me than a 9 that isn't true.

**4 — Energy** → save to `checkin_energy` (Number, 1-5)
> Energy levels this week, 1-5?

**5 — Mood** → save to `checkin_mood` (Number, 1-5)
> Mood, 1-5?

**6 — Wins** → save to `checkin_wins` (Text)
> One thing that went well this week?

**7 — Struggles** → save to `checkin_struggles` (Text)
> One thing that got in the way? Be specific — "weekends" tells me more
> than "motivation".

**8 — Close** → Action: apply tag `checkin-completed`, set
`checkin_date` to today
> Got it, logged. I'll look at this before our next session.
> If something comes up before then, just message me here.

### Why the questions are worded that way

The adherence and struggles prompts explicitly invite an unflattering
answer. A check-in that only collects good news is a check-in that tells
you nothing you can coach on — and clients pattern-match fast to what
you actually want to hear.

## Step 6 — getting the data into Airtable

**On Free tier (manual, weekly):**

1. ManyChat → Audience → filter by tag `checkin-completed`
2. Export CSV (includes the custom User Fields)
3. In Airtable, import into `Check-ins` and `Progress Tracking`, matching
   on `ManyChat Subscriber ID`
4. Remove the `checkin-completed` tag so next week starts clean

Budget about 10 minutes a week. That's the free-tier tax.

**On Pro (automatic):** add an **External Request** action as the last
flow step, POSTing the fields to the Airtable API (or a Make webhook —
Make is already connected on this account). That removes step 6 entirely
and is the main reason to upgrade.

## Step 7 — the reminder itself

ManyChat can't send it. Options, cheapest first:

- **IG Story** with the "reply CHECKIN" prompt. Free, and the reply is
  what opens the messaging window. Start here.
- **Email from Airtable** — a scheduled automation over `Check-ins`,
  using the `Reminder Sent` checkbox as a guard. Free, but see the note
  below about the base's data.
- **Telegram** — no 24-hour window, free Bot API, and `Telegram Chat ID`
  already exists on `Clients`. Already the documented Phase 2 in the root
  `README.md`, and the only option that closes the loop end to end.

## Before any of this runs against real people

The `Clients` and `Check-ins` tables currently hold **15 records each,
all bulk-created in the same second, all marked `Needs Verification`,
all with `Subscription Status: Unknown`, and every check-in date falling
in 2024.** That is seed data.

Confirm which records are real and mark them `Verified Current` before
pointing any automation at them. Any reminder automation built here
should filter on `Data Verification Status = Verified Current` so it
structurally cannot message an unverified record.

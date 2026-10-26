"""Build the Job Command hook bank and 4-week short-form content calendar.

Talent: Cletus (on-screen avatar), voiced by ElevenLabs voice 46WLznXSbPOBU4NB5X1e.

Outputs:
  content/hook_bank.csv           - reusable hooks, grouped by hook type
  content/content_calendar.csv    - dated posting schedule
  content/commercial_payloads.csv - calendar rows in the exact schema the
                                    commercial engine reads (video_id,
                                    visual_prompt, hud_overlay_text,
                                    voiceover_script)
"""
import csv
import datetime as dt
from pathlib import Path

OUT = Path(__file__).parent
START = dt.date(2026, 10, 27)  # Tuesday; posts run Tue-Sat
VOICE_ID = "46WLznXSbPOBU4NB5X1e"
CLETUS = "Cletus (match reference image exactly: same face, red shorts, work boots)"
STYLE = "9:16 vertical, handheld phone feel, natural daylight, fast cuts"
PLATFORMS = "TikTok / IG Reels / YT Shorts"

HOOKS = [
    # (hook_type, on-screen hook, why it works)
    ("Pain callout", "Still writin' quotes in your truck at 9 at night?", "Names a specific, familiar pain in the first 2s"),
    ("Pain callout", "Your crew went to the wrong house. Again.", "Instant recognition for anyone running a crew"),
    ("Pain callout", "You did the work. Why you still chasin' the money?", "Late payment is the most shared frustration"),
    ("Pain callout", "Three apps, a spreadsheet, and a whiteboard ain't a system.", "Calls out tool sprawl"),
    ("Pain callout", "Job's done. Invoice ain't. Sound familiar?", "Short, rhythmic, relatable"),
    ("Pattern interrupt", "Hold up. Put the clipboard down.", "Command + visual prop breaks the scroll"),
    ("Pattern interrupt", "This here's what my Sundays used to look like.", "Before shot sets up a transformation"),
    ("Pattern interrupt", "I fired my whiteboard.", "Absurd line makes people stay for the payoff"),
    ("Pattern interrupt", "Watch me book, send, and bill a job 'fore this video ends.", "Built-in timer keeps watch time high"),
    ("Contrarian", "Hot take: more software's why you're drownin'.", "Disagreement drives comments"),
    ("Contrarian", "You don't need more leads. You need to quit losin' the ones you got.", "Flips the usual advice"),
    ("Contrarian", "Hirin' more office help ain't gonna fix this.", "Challenges a costly assumption"),
    ("Contrarian", "Best contractors I know don't answer the phone on the job.", "Curiosity plus authority"),
    ("Versus", "I quit my old field-service app. Here's what changed.", "Comparison without naming a brand"),
    ("Versus", "Same job, two apps. Count the taps.", "Side-by-side demo the viewer can check"),
    ("Versus", "Built by folks who've actually been up on a roof.", "Positions against office-built tools"),
    ("POV", "POV: your schedule fixes itself when a job runs long.", "Puts the viewer in the outcome"),
    ("POV", "POV: customer signed the quote 'fore you left the driveway.", "Shows a concrete win"),
    ("POV", "POV: you're on the job site and your office fits in your pocket.", "Pairs with job-site b-roll"),
    ("POV", "POV: it's Friday and every invoice is paid.", "Aspirational, end-of-week timing"),
    ("Curiosity gap", "The one screen I check 'fore every job.", "Viewer waits for the reveal"),
    ("Curiosity gap", "This one button saved me a whole day last week.", "Small action, big payoff"),
    ("Curiosity gap", "Nobody tells new contractors this 'bout schedulin'.", "Insider knowledge framing"),
    ("Curiosity gap", "Almost didn't post this. My competition's gonna use it.", "Exclusivity drives saves"),
    ("Challenge", "Run your whole outfit from your phone for one week. I dare ya.", "Invites participation and duets"),
    ("Challenge", "Time yourself writin' a quote. Now watch me.", "Creates a direct comparison"),
    ("Challenge", "Tell me your trade in the comments. I'll show you your setup.", "Comment bait that yields follow-up videos"),
    ("Story", "Day one of runnin' my business off one app.", "Series format brings people back"),
    ("Story", "The text from a customer that made me change everything.", "Emotional, narrative pull"),
    ("Story", "Lost a [REAL $ AMOUNT] job over one missed callback. Never again.", "Specific stakes; use a true number only"),
    ("Story", "Day ten on one app. Here's what broke.", "Series payoff; rewards people who followed day one"),
]

# Each post: (pillar, hook_index, voiceover, visual, hud, cta)
# Voiceovers stay at or under ~20 words so they fit a single ~8s generated clip.
POSTS = [
    ("Pain", 0, "Quotes in the truck at nine at night? Nah. Job Command does it on site. They sign 'fore I leave.",
     f"{CLETUS} in a dark truck cab with a clipboard, then cut to sunny driveway tapping a phone", "QUOTE SENT // 00:47", "Link in bio"),
    ("Demo", 8, "Book it, send the crew, bill it. One app. Under a minute. Watch.",
     f"{CLETUS} on a job site, phone in hand, quick taps, stopwatch visible on screen", "BOOK > DISPATCH > INVOICE", "Follow for part 2"),
    ("Job-site POV", 18, "This right here's my office now. Schedule, crew, payments. All in my pocket.",
     "first-person job-site b-roll, gloved hand holding phone over lumber and tools", "OFFICE: MOBILE", "Save this"),
    ("Contrarian", 9, "More apps ain't more control. One system is. That's why we built Job Command.",
     f"{CLETUS} sweeping sticky notes and a laptop off a truck tailgate", "APPS: 4 > 1", "Comment your stack"),
    ("Community", 26, "Tell me your trade down in the comments. I'll show y'all how I'd set it up.",
     f"{CLETUS} pointing at camera on a job site, comment bubbles popping in", "PLUMBER? HVAC? ROOFER?", "Comment your trade"),
    ("Pain", 2, "You did the work. Quit chasin' the money. Job Command sends the bill and the reminder.",
     f"{CLETUS} wiping hands after a job, phone buzzes with a payment notification", "PAYMENT RECEIVED", "Link in bio"),
    ("Versus", 14, "Same job, two apps. Count the taps. I'll wait.",
     "split-screen of two phones, one needs many taps, one needs few", "TAPS: [COUNT] vs [COUNT]", "Which one you on?"),
    ("Story", 27, "Day one runnin' my whole business off one app. Let's see if it holds up.",
     f"{CLETUS} at sunrise loading a truck, vlog-style talking to camera", "DAY 01", "Follow the series"),
    ("Job-site POV", 17, "Quote got signed 'fore I even backed outta the driveway.",
     "first-person view from a truck pulling out of a driveway, phone shows 'Approved'", "QUOTE: APPROVED", "Save this"),
    ("Founder", 15, "Built by folks who've been up on a roof. Not sittin' in some boardroom.",
     f"{CLETUS} on a roof at golden hour, looks out, then turns to camera", "BUILT IN THE FIELD", "Follow"),
    ("Pain", 1, "Wrong house. Again. Job Command sends your crew the right address, with directions, every time.",
     "work truck pulling up to the wrong house, driver squinting at phone", "DISPATCH: CORRECTED", "Link in bio"),
    ("Demo", 21, "One button. Job runs long, the whole day reshuffles itself.",
     f"close-up of {CLETUS}'s thumb tapping a phone, calendar blocks sliding into place", "SCHEDULE: AUTO-SHIFT", "Save this"),
    ("Job-site POV", 20, "The one screen I check 'fore every single job.",
     "first-person, phone held over a truck dashboard showing the day's job list", "TODAY: 6 JOBS", "Follow"),
    ("Contrarian", 10, "You don't need more leads, partner. You need to quit losin' the ones you got.",
     f"{CLETUS} catching a missed-call notification on a job site", "MISSED CALLS: 0", "Comment if this is you"),
    ("Story", 30, "Day ten on one app. Here's what broke and what didn't.",
     f"{CLETUS} sitting on a tailgate at dusk, talking to camera", "DAY 10", "Follow the series"),
    ("Pain", 3, "Three apps, a spreadsheet, and a whiteboard ain't a system. This is.",
     "messy office whiteboard and sticky notes, hard cut to a clean phone screen", "SYSTEM: ONLINE", "Link in bio"),
    ("Challenge", 25, "Time yourself writin' a quote. Go 'head. Now watch me.",
     f"{CLETUS} starting a stopwatch, tapping phone fast on a job site", "QUOTE TIMER", "Duet this"),
    ("Job-site POV", 19, "It's Friday. Every invoice is paid. That's the whole video.",
     "first-person, phone showing paid invoices, truck tailgate closing at sunset", "INVOICES: PAID", "Save this"),
    ("Versus", 13, "Quit my old field-service app. Here's what changed in thirty days.",
     f"{CLETUS} deleting an app icon from a phone, then working smooth on site", "30 DAYS IN", "Link in bio"),
    ("Founder", 29, "Lost a big job over one missed callback. So we built somethin' that don't forget.",
     f"{CLETUS} leaning on a truck, serious, then cut to phone showing a callback reminder", "NEVER AGAIN", "Follow"),
]


def post_dates():
    d = START
    while True:
        if d.weekday() in (1, 2, 3, 4, 5):  # Tue-Sat
            yield d
        d += dt.timedelta(days=1)


def main():
    with open(OUT / "hook_bank.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["hook_id", "hook_type", "hook", "why_it_works"])
        for i, (htype, hook, why) in enumerate(HOOKS, 1):
            w.writerow([f"H{i:02d}", htype, hook, why])

    cal_rows, payload_rows = [], []
    for n, (date, (pillar, hi, vo, visual, hud, cta)) in enumerate(zip(post_dates(), POSTS), 1):
        vid = f"JC_{date:%Y%m%d}_{n:02d}"
        htype, hook, _ = HOOKS[hi]
        week = (date - START).days // 7 + 1
        cal_rows.append([
            f"Week {week}", date.isoformat(), f"{date:%a}", "6:30 PM local",
            PLATFORMS, pillar, f"H{hi + 1:02d}", htype, hook,
            vo, hud, cta, VOICE_ID, vid, "Draft",
        ])
        payload_rows.append([vid, f"{visual}, {STYLE}", hud, vo])

    with open(OUT / "content_calendar.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["week", "date", "day", "post_time", "platforms", "pillar",
                    "hook_id", "hook_type", "on_screen_hook", "voiceover_script",
                    "hud_overlay_text", "cta", "voice_id", "video_id", "status"])
        w.writerows(cal_rows)

    with open(OUT / "commercial_payloads.csv", "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["video_id", "visual_prompt", "hud_overlay_text", "voiceover_script"])
        w.writerows(payload_rows)


if __name__ == "__main__":
    main()

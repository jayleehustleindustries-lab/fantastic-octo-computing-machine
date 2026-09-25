"use client";

import { useEffect, useMemo, useState } from "react";
import {
  Pick,
  breakevenProbability,
  computeStats,
  formatMoney,
  formatPercent,
  profitFor,
} from "@/lib/odds";

type FormState = {
  event_date: string;
  sport: string;
  matchup: string;
  platform: string;
  player: string;
  market: string;
  line: string;
  side: string;
  odds_format: "american" | "multiplier";
  odds_value: string;
  legs_in_parlay: string;
  stake: string;
  potential_payout: string;
  notes: string;
};

const emptyForm: FormState = {
  event_date: new Date().toISOString().slice(0, 10),
  sport: "",
  matchup: "",
  platform: "",
  player: "",
  market: "",
  line: "",
  side: "",
  odds_format: "american",
  odds_value: "",
  legs_in_parlay: "1",
  stake: "",
  potential_payout: "",
  notes: "",
};

function autoPayout(form: FormState): string {
  const stake = Number(form.stake);
  const odds = Number(form.odds_value);
  if (!stake || !odds) return "";
  if (form.odds_format === "american") {
    const payout = odds > 0 ? stake * (odds / 100 + 1) : stake * (100 / -odds + 1);
    return payout.toFixed(2);
  }
  return (stake * odds).toFixed(2);
}

export default function Dashboard() {
  const [picks, setPicks] = useState<Pick[]>([]);
  const [loading, setLoading] = useState(true);
  const [form, setForm] = useState<FormState>(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function load() {
    setLoading(true);
    const res = await fetch("/api/picks");
    const data = await res.json();
    setPicks(data.picks ?? []);
    setLoading(false);
  }

  useEffect(() => {
    load();
  }, []);

  const stats = useMemo(() => computeStats(picks), [picks]);

  function updateField<K extends keyof FormState>(key: K, value: FormState[K]) {
    setForm((f) => {
      const next = { ...f, [key]: value };
      if (key === "stake" || key === "odds_value" || key === "odds_format") {
        next.potential_payout = autoPayout(next);
      }
      return next;
    });
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    const res = await fetch("/api/picks", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(form),
    });
    setSubmitting(false);
    if (!res.ok) {
      const data = await res.json();
      setError(data.error ?? "Failed to save pick");
      return;
    }
    setForm({ ...emptyForm, event_date: form.event_date });
    load();
  }

  async function grade(id: string, result: "win" | "loss" | "push") {
    await fetch(`/api/picks/${id}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ result }),
    });
    load();
  }

  async function remove(id: string) {
    await fetch(`/api/picks/${id}`, { method: "DELETE" });
    load();
  }

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 space-y-8">
      <header>
        <h1 className="text-2xl font-semibold">Vig Tracker</h1>
        <p className="text-sm text-slate-400">
          Log every pick. See whether you&apos;re actually clearing the breakeven the odds require — not vibes.
        </p>
      </header>

      <section className="grid grid-cols-2 gap-3 sm:grid-cols-4">
        <Stat label="Record" value={`${stats.wins}-${stats.losses}-${stats.pushes}`} sub={`${stats.pending} pending`} />
        <Stat label="Hit rate" value={formatPercent(stats.hitRate)} />
        <Stat label="Avg breakeven req." value={formatPercent(stats.avgBreakevenRequired)} />
        <Stat
          label="Edge"
          value={stats.edge === null ? "—" : `${stats.edge >= 0 ? "+" : ""}${formatPercent(stats.edge)}`}
          tone={stats.edge === null ? "neutral" : stats.edge >= 0 ? "good" : "bad"}
        />
        <Stat label="Staked" value={formatMoney(stats.totalStaked)} />
        <Stat
          label="Profit"
          value={formatMoney(stats.totalProfit)}
          tone={stats.totalProfit > 0 ? "good" : stats.totalProfit < 0 ? "bad" : "neutral"}
        />
        <Stat
          label="ROI"
          value={stats.roi === null ? "—" : `${stats.roi >= 0 ? "+" : ""}${formatPercent(stats.roi)}`}
          tone={stats.roi === null ? "neutral" : stats.roi >= 0 ? "good" : "bad"}
        />
        <Stat label="Total picks" value={String(stats.total)} />
      </section>

      <section className="rounded-xl border border-slate-800 bg-slate-900 p-4">
        <h2 className="mb-3 text-sm font-medium text-slate-300">Log a pick</h2>
        <form onSubmit={onSubmit} className="grid grid-cols-2 gap-3 sm:grid-cols-4">
          <LabeledInput label="Date" type="date" value={form.event_date} onChange={(v) => updateField("event_date", v)} required />
          <LabeledInput label="Sport" placeholder="WNBA" value={form.sport} onChange={(v) => updateField("sport", v)} required />
          <LabeledInput label="Matchup" placeholder="LV @ PHX" value={form.matchup} onChange={(v) => updateField("matchup", v)} required />
          <LabeledInput label="Platform" placeholder="Dabble / FanDuel" value={form.platform} onChange={(v) => updateField("platform", v)} required />
          <LabeledInput label="Player (optional)" value={form.player} onChange={(v) => updateField("player", v)} />
          <LabeledInput label="Market" placeholder="Points+Rebounds" value={form.market} onChange={(v) => updateField("market", v)} required />
          <LabeledInput label="Line (optional)" type="number" step="0.5" value={form.line} onChange={(v) => updateField("line", v)} />
          <LabeledInput label="Side" placeholder="Over / Team name" value={form.side} onChange={(v) => updateField("side", v)} required />

          <div className="flex flex-col gap-1">
            <label className="text-xs text-slate-400">Odds format</label>
            <select
              value={form.odds_format}
              onChange={(e) => updateField("odds_format", e.target.value as "american" | "multiplier")}
              className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-500"
            >
              <option value="american">American (-110 / +330)</option>
              <option value="multiplier">Multiplier (payout board)</option>
            </select>
          </div>
          <LabeledInput
            label={form.odds_format === "american" ? "Odds (e.g. -110)" : "Multiplier (e.g. 3 for 3x)"}
            type="number"
            step="any"
            value={form.odds_value}
            onChange={(v) => updateField("odds_value", v)}
            required
          />
          <LabeledInput label="Legs in parlay" type="number" min="1" value={form.legs_in_parlay} onChange={(v) => updateField("legs_in_parlay", v)} />
          <LabeledInput label="Stake ($)" type="number" step="0.01" value={form.stake} onChange={(v) => updateField("stake", v)} required />
          <LabeledInput label="Potential payout ($)" type="number" step="0.01" value={form.potential_payout} onChange={(v) => updateField("potential_payout", v)} required />
          <div className="col-span-2 sm:col-span-4">
            <LabeledInput label="Notes (optional)" value={form.notes} onChange={(v) => updateField("notes", v)} />
          </div>

          {error && <p className="col-span-2 text-sm text-red-400 sm:col-span-4">{error}</p>}

          <div className="col-span-2 sm:col-span-4">
            <button
              type="submit"
              disabled={submitting}
              className="rounded-lg bg-slate-100 px-4 py-2 text-sm font-medium text-slate-950 disabled:opacity-50"
            >
              {submitting ? "Saving…" : "Add pick"}
            </button>
          </div>
        </form>
      </section>

      <section>
        <h2 className="mb-3 text-sm font-medium text-slate-300">History</h2>
        {loading ? (
          <p className="text-sm text-slate-400">Loading…</p>
        ) : picks.length === 0 ? (
          <p className="text-sm text-slate-400">No picks logged yet.</p>
        ) : (
          <div className="overflow-x-auto rounded-xl border border-slate-800">
            <table className="min-w-full text-sm">
              <thead className="bg-slate-900 text-left text-xs uppercase text-slate-400">
                <tr>
                  <th className="px-3 py-2">Date</th>
                  <th className="px-3 py-2">Matchup</th>
                  <th className="px-3 py-2">Pick</th>
                  <th className="px-3 py-2">Odds</th>
                  <th className="px-3 py-2">Breakeven</th>
                  <th className="px-3 py-2">Stake</th>
                  <th className="px-3 py-2">Result</th>
                  <th className="px-3 py-2">Profit</th>
                  <th className="px-3 py-2"></th>
                </tr>
              </thead>
              <tbody>
                {picks.map((p) => (
                  <tr key={p.id} className="border-t border-slate-800">
                    <td className="whitespace-nowrap px-3 py-2 text-slate-400">{p.event_date}</td>
                    <td className="px-3 py-2">
                      {p.platform} · {p.sport} · {p.matchup}
                    </td>
                    <td className="px-3 py-2">
                      {p.player ? `${p.player} ` : ""}
                      {p.market} {p.line ?? ""} {p.side}
                      {p.legs_in_parlay > 1 && (
                        <span className="ml-1 text-xs text-slate-500">({p.legs_in_parlay}-leg)</span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-400">
                      {p.odds_format === "american"
                        ? p.odds_value > 0
                          ? `+${p.odds_value}`
                          : p.odds_value
                        : `${p.odds_value}x`}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-400">
                      {formatPercent(breakevenProbability(p))}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2 text-slate-400">{formatMoney(Number(p.stake))}</td>
                    <td className="whitespace-nowrap px-3 py-2">
                      {p.result === "pending" ? (
                        <div className="flex gap-1">
                          <button onClick={() => grade(p.id, "win")} className="rounded bg-emerald-900/50 px-2 py-1 text-xs text-emerald-300 hover:bg-emerald-900">
                            Win
                          </button>
                          <button onClick={() => grade(p.id, "loss")} className="rounded bg-red-900/50 px-2 py-1 text-xs text-red-300 hover:bg-red-900">
                            Loss
                          </button>
                          <button onClick={() => grade(p.id, "push")} className="rounded bg-slate-800 px-2 py-1 text-xs text-slate-300 hover:bg-slate-700">
                            Push
                          </button>
                        </div>
                      ) : (
                        <span
                          className={
                            p.result === "win"
                              ? "text-emerald-400"
                              : p.result === "loss"
                              ? "text-red-400"
                              : "text-slate-400"
                          }
                        >
                          {p.result}
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2">
                      {p.result === "pending" ? (
                        "—"
                      ) : (
                        <span className={profitFor(p) >= 0 ? "text-emerald-400" : "text-red-400"}>
                          {formatMoney(profitFor(p))}
                        </span>
                      )}
                    </td>
                    <td className="whitespace-nowrap px-3 py-2">
                      <button onClick={() => remove(p.id)} className="text-xs text-slate-500 hover:text-red-400">
                        delete
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}

function Stat({
  label,
  value,
  sub,
  tone = "neutral",
}: {
  label: string;
  value: string;
  sub?: string;
  tone?: "good" | "bad" | "neutral";
}) {
  const toneClass =
    tone === "good" ? "text-emerald-400" : tone === "bad" ? "text-red-400" : "text-slate-100";
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-900 p-4">
      <p className="text-xs text-slate-400">{label}</p>
      <p className={`mt-1 text-xl font-semibold ${toneClass}`}>{value}</p>
      {sub && <p className="text-xs text-slate-500">{sub}</p>}
    </div>
  );
}

function LabeledInput({
  label,
  value,
  onChange,
  type = "text",
  placeholder,
  required,
  step,
  min,
}: {
  label: string;
  value: string;
  onChange: (v: string) => void;
  type?: string;
  placeholder?: string;
  required?: boolean;
  step?: string;
  min?: string;
}) {
  return (
    <div className="flex flex-col gap-1">
      <label className="text-xs text-slate-400">{label}</label>
      <input
        type={type}
        value={value}
        placeholder={placeholder}
        required={required}
        step={step}
        min={min}
        onChange={(e) => onChange(e.target.value)}
        className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm outline-none focus:border-slate-500"
      />
    </div>
  );
}

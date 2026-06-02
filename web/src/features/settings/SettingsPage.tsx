import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { isApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { Card, CardHeader } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useMe, useUpdateRiskProfile } from "../../hooks/useAuth";
import {
  useNotificationPreferences,
  useUpdateNotificationPreferences,
} from "../../hooks/useNotifications";
import type { RiskTolerance, TimeHorizon } from "../../models/enums";
import type { NotificationPreference } from "../../models/notification";
import { useAuthStore } from "../../store/authStore";

const TOLERANCES: RiskTolerance[] = ["conservative", "moderate", "aggressive"];
const HORIZONS: TimeHorizon[] = ["short", "medium", "long"];
const OBJECTIVES = ["growth", "income", "preservation", "speculation"];

export function SettingsPage() {
  const me = useMe();
  const update = useUpdateRiskProfile();
  const logout = useAuthStore((s) => s.logout);

  const [tolerance, setTolerance] = useState<RiskTolerance>("moderate");
  const [horizon, setHorizon] = useState<TimeHorizon>("long");
  const [objectives, setObjectives] = useState<string[]>([]);
  const [maxPosition, setMaxPosition] = useState<string>("");

  useEffect(() => {
    const rp = me.data?.risk_profile;
    if (rp) {
      setTolerance(rp.risk_tolerance);
      setHorizon(rp.time_horizon);
      setObjectives(rp.objectives ?? []);
      setMaxPosition(rp.max_position_pct != null ? String(rp.max_position_pct) : "");
    }
  }, [me.data]);

  const toggleObjective = (value: string) => {
    setObjectives((prev) =>
      prev.includes(value) ? prev.filter((o) => o !== value) : [...prev, value],
    );
  };

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    update.mutate({
      risk_tolerance: tolerance,
      time_horizon: horizon,
      objectives,
      max_position_pct: maxPosition === "" ? null : Number(maxPosition),
    });
  };

  return (
    <div className="space-y-5">
      <header>
        <h1 className="text-2xl font-semibold">Settings</h1>
        <p className="text-sm text-muted">{me.data?.email ?? me.data?.display_name ?? ""}</p>
      </header>

      {me.isLoading && <Spinner />}

      <Card>
        <CardHeader title="Risk profile" />
        <p className="mb-4 text-sm text-muted">
          Drives the AI committee's personalization (portfolio fit &amp; risk).
        </p>
        <form onSubmit={onSubmit} className="space-y-4">
          <Field label="Risk tolerance">
            <Select value={tolerance} onChange={(v) => setTolerance(v as RiskTolerance)} options={TOLERANCES} />
          </Field>
          <Field label="Time horizon">
            <Select value={horizon} onChange={(v) => setHorizon(v as TimeHorizon)} options={HORIZONS} />
          </Field>
          <Field label="Objectives">
            <div className="flex flex-wrap gap-2">
              {OBJECTIVES.map((obj) => (
                <button
                  type="button"
                  key={obj}
                  onClick={() => toggleObjective(obj)}
                  className={`rounded-full px-3 py-1 text-sm capitalize transition-colors ${
                    objectives.includes(obj)
                      ? "bg-primary text-white"
                      : "bg-surface-2 text-muted hover:text-slate-200"
                  }`}
                >
                  {obj}
                </button>
              ))}
            </div>
          </Field>
          <Input
            label="Max position size (% of portfolio, optional)"
            type="number"
            min="0"
            max="100"
            step="any"
            value={maxPosition}
            onChange={(e) => setMaxPosition(e.target.value)}
          />
          {update.isError && (
            <ErrorPanel
              message={isApiError(update.error) ? update.error.message : "Could not save."}
            />
          )}
          <div className="flex items-center gap-3">
            <Button type="submit" loading={update.isPending}>
              Save
            </Button>
            {update.isSuccess && <span className="text-sm text-bull">Saved ✓</span>}
          </div>
        </form>
      </Card>

      <NotificationPreferencesCard />

      <Card>
        <CardHeader title="Account" />
        <Button variant="danger" onClick={logout}>
          Sign out
        </Button>
      </Card>
    </div>
  );
}

const CATEGORIES = [
  { key: "rating_change", label: "Rating changes" },
  { key: "news", label: "News impact" },
];

function NotificationPreferencesCard() {
  const prefs = useNotificationPreferences();
  const update = useUpdateNotificationPreferences();

  const [categories, setCategories] = useState<string[]>([]);
  const [minPriority, setMinPriority] = useState("high");
  const [maxRisk, setMaxRisk] = useState("high");
  const [quietStart, setQuietStart] = useState("");
  const [quietEnd, setQuietEnd] = useState("");

  useEffect(() => {
    const p = prefs.data;
    if (p) {
      setCategories(p.categories ?? []);
      setMinPriority(p.min_priority);
      setMaxRisk(p.max_risk);
      setQuietStart(p.quiet_hours_start != null ? String(p.quiet_hours_start) : "");
      setQuietEnd(p.quiet_hours_end != null ? String(p.quiet_hours_end) : "");
    }
  }, [prefs.data]);

  const toggle = (key: string) =>
    setCategories((prev) => (prev.includes(key) ? prev.filter((c) => c !== key) : [...prev, key]));

  const onSave = (e: FormEvent) => {
    e.preventDefault();
    const payload: NotificationPreference = {
      categories,
      min_priority: minPriority as NotificationPreference["min_priority"],
      max_risk: maxRisk as NotificationPreference["max_risk"],
      sectors: [],
      quiet_hours_start: quietStart === "" ? null : Number(quietStart),
      quiet_hours_end: quietEnd === "" ? null : Number(quietEnd),
    };
    update.mutate(payload);
  };

  return (
    <Card>
      <CardHeader title="Notifications" />
      <p className="mb-4 text-sm text-muted">
        Choose what the hourly AI run alerts you about. Empty categories = all.
      </p>
      {prefs.isLoading && <Spinner />}
      <form onSubmit={onSave} className="space-y-4">
        <Field label="Categories">
          <div className="flex flex-wrap gap-2">
            {CATEGORIES.map((c) => (
              <button
                type="button"
                key={c.key}
                onClick={() => toggle(c.key)}
                className={`rounded-full px-3 py-1 text-sm transition-colors ${
                  categories.includes(c.key)
                    ? "bg-primary text-white"
                    : "bg-surface-2 text-muted hover:text-slate-200"
                }`}
              >
                {c.label}
              </button>
            ))}
          </div>
        </Field>
        <div className="grid grid-cols-2 gap-3">
          <Field label="Min priority">
            <Select
              value={minPriority}
              onChange={setMinPriority}
              options={["normal", "high", "critical"]}
            />
          </Field>
          <Field label="Max risk">
            <Select value={maxRisk} onChange={setMaxRisk} options={["low", "medium", "high"]} />
          </Field>
          <Input
            label="Quiet from (UTC hour)"
            type="number"
            min="0"
            max="23"
            value={quietStart}
            onChange={(e) => setQuietStart(e.target.value)}
          />
          <Input
            label="Quiet until (UTC hour)"
            type="number"
            min="0"
            max="23"
            value={quietEnd}
            onChange={(e) => setQuietEnd(e.target.value)}
          />
        </div>
        <div className="flex items-center gap-3">
          <Button type="submit" loading={update.isPending}>
            Save
          </Button>
          {update.isSuccess && <span className="text-sm text-bull">Saved ✓</span>}
        </div>
      </form>
    </Card>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <div>
      <span className="mb-1 block text-sm text-muted">{label}</span>
      {children}
    </div>
  );
}

function Select({
  value,
  onChange,
  options,
}: {
  value: string;
  onChange: (value: string) => void;
  options: string[];
}) {
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      className="w-full rounded-lg border border-border bg-surface-2 px-3 py-2 text-sm capitalize text-slate-100 outline-none focus:border-primary"
    >
      {options.map((opt) => (
        <option key={opt} value={opt} className="capitalize">
          {opt}
        </option>
      ))}
    </select>
  );
}

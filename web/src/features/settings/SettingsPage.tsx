import { type FormEvent, type ReactNode, useEffect, useState } from "react";

import { isApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { Card, CardHeader } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { ErrorPanel, Spinner } from "../../components/ui/StatePanel";
import { useMe, useUpdateRiskProfile } from "../../hooks/useAuth";
import type { RiskTolerance, TimeHorizon } from "../../models/enums";
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

      <Card>
        <CardHeader title="Account" />
        <Button variant="danger" onClick={logout}>
          Sign out
        </Button>
      </Card>
    </div>
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

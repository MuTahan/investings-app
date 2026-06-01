import { type FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import { isApiError } from "../../api/errors";
import { Button } from "../../components/ui/Button";
import { Input } from "../../components/ui/Input";
import { ErrorPanel } from "../../components/ui/StatePanel";
import { useRegister } from "../../hooks/useAuth";
import { AuthScaffold } from "./LoginPage";

export function RegisterPage() {
  const register = useRegister();
  const [displayName, setDisplayName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    register.mutate({
      email,
      password,
      display_name: displayName || undefined,
    });
  };

  return (
    <AuthScaffold title="Create your account" subtitle="Start tracking and analyzing US markets">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Name"
          autoComplete="name"
          value={displayName}
          onChange={(e) => setDisplayName(e.target.value)}
        />
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password (min 8 characters)"
          type="password"
          autoComplete="new-password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {register.isError && (
          <ErrorPanel
            message={isApiError(register.error) ? register.error.message : "Sign up failed."}
          />
        )}
        <Button type="submit" className="w-full" loading={register.isPending}>
          Create account
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-muted">
        Already have an account?{" "}
        <Link to="/login" className="text-primary hover:underline">
          Sign in
        </Link>
      </p>
    </AuthScaffold>
  );
}

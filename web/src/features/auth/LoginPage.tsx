import { type FormEvent, type ReactNode, useState } from "react";
import { Link } from "react-router-dom";

import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { Input } from "../../components/ui/Input";
import { ErrorPanel } from "../../components/ui/StatePanel";
import { useLogin } from "../../hooks/useAuth";
import { isApiError } from "../../api/errors";

export function LoginPage() {
  const login = useLogin();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const onSubmit = (e: FormEvent) => {
    e.preventDefault();
    login.mutate({ email, password });
  };

  return (
    <AuthScaffold title="Welcome back" subtitle="Sign in to your Investing AI account">
      <form onSubmit={onSubmit} className="space-y-4">
        <Input
          label="Email"
          type="email"
          autoComplete="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
        />
        <Input
          label="Password"
          type="password"
          autoComplete="current-password"
          required
          value={password}
          onChange={(e) => setPassword(e.target.value)}
        />
        {login.isError && (
          <ErrorPanel
            message={isApiError(login.error) ? login.error.message : "Sign in failed."}
          />
        )}
        <Button type="submit" className="w-full" loading={login.isPending}>
          Sign in
        </Button>
      </form>
      <p className="mt-4 text-center text-sm text-muted">
        No account?{" "}
        <Link to="/register" className="text-primary hover:underline">
          Create one
        </Link>
      </p>
    </AuthScaffold>
  );
}

export function AuthScaffold({
  title,
  subtitle,
  children,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-[100dvh] items-center justify-center px-4">
      <div className="w-full max-w-sm">
        <div className="mb-6 flex flex-col items-center gap-2 text-center">
          <img src="/favicon.svg" alt="" className="h-12 w-12" />
          <h1 className="text-xl font-semibold">{title}</h1>
          <p className="text-sm text-muted">{subtitle}</p>
        </div>
        <Card>{children}</Card>
      </div>
    </div>
  );
}

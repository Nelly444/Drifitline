import axios from "axios";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PrimaryButton } from "../components/PrimaryButton";
import { TextField } from "../components/TextField";
import { useAuth } from "../contexts/AuthContext";

export function Login() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      navigate("/");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 400) {
        setError("Incorrect email or password.");
      } else {
        setError("Something went wrong. Check your connection and try again.");
      }
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-canvas">
      <div className="w-full max-w-sm rounded-card border border-hairline bg-surface p-8">
        <p className="text-heading-sm font-serif font-medium text-ink">Driftline</p>
        <h1 className="mt-6 text-heading-sm font-serif font-medium text-ink">Log in</h1>

        <form className="mt-6 flex flex-col gap-4" onSubmit={handleSubmit}>
          <TextField
            label="Email"
            type="email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoFocus
          />
          <TextField
            label="Password"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-body-sm font-sans text-rust">{error}</p>}
          <PrimaryButton type="submit" disabled={submitting} className="mt-2 w-full disabled:opacity-60">
            {submitting ? "Logging in…" : "Log in"}
          </PrimaryButton>
        </form>

        <p className="mt-6 text-body-sm font-sans text-slate">
          Don't have an account?{" "}
          <Link to="/register" className="font-medium text-signal-blue">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}

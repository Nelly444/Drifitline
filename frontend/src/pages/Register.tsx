import axios from "axios";
import { useState, type FormEvent } from "react";
import { Link, useNavigate } from "react-router-dom";
import { PrimaryButton } from "../components/PrimaryButton";
import { TextField } from "../components/TextField";
import { useAuth } from "../contexts/AuthContext";

export function Register() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const { register } = useAuth();
  const navigate = useNavigate();

  async function handleSubmit(event: FormEvent) {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password);
      navigate("/");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 400) {
        const detail = err.response.data?.detail;
        const code = typeof detail === "string" ? detail : detail?.code;
        if (code === "REGISTER_USER_ALREADY_EXISTS") {
          setError("An account with that email already exists.");
        } else if (code === "REGISTER_INVALID_PASSWORD") {
          setError(detail?.reason ?? "That password isn't allowed. Please choose another.");
        } else {
          setError("Could not create an account with that email.");
        }
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
        <h1 className="mt-6 text-heading-sm font-serif font-medium text-ink">Create an account</h1>

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
            minLength={8}
          />
          {error && <p className="text-body-sm font-sans text-rust">{error}</p>}
          <PrimaryButton type="submit" disabled={submitting} className="mt-2 w-full disabled:opacity-60">
            {submitting ? "Creating account…" : "Sign up"}
          </PrimaryButton>
        </form>

        <p className="mt-6 text-body-sm font-sans text-slate">
          Already have an account?{" "}
          <Link to="/login" className="font-medium text-signal-blue">
            Log in
          </Link>
        </p>
      </div>
    </div>
  );
}

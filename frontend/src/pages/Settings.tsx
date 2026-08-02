import axios from "axios";
import { useEffect, useState, type FormEvent } from "react";
import { useNavigate } from "react-router-dom";
import { PrimaryButton } from "../components/PrimaryButton";
import { TextField } from "../components/TextField";
import { useAuth } from "../contexts/AuthContext";
import {
  deleteAccount,
  disconnectPlaidAccount,
  fetchCurrentUser,
  fetchPlaidStatus,
  updatePassword,
} from "../lib/api";
import type { CurrentUser, PlaidStatus } from "../lib/types";

export function Settings() {
  const [user, setUser] = useState<CurrentUser | null>(null);
  const [plaidStatus, setPlaidStatus] = useState<PlaidStatus | null>(null);
  const [loadError, setLoadError] = useState<string | null>(null);

  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [passwordError, setPasswordError] = useState<string | null>(null);
  const [passwordSuccess, setPasswordSuccess] = useState(false);
  const [savingPassword, setSavingPassword] = useState(false);

  const [disconnecting, setDisconnecting] = useState(false);
  const [disconnectError, setDisconnectError] = useState<string | null>(null);

  const [deleteConfirmEmail, setDeleteConfirmEmail] = useState("");
  const [deleting, setDeleting] = useState(false);
  const [deleteError, setDeleteError] = useState<string | null>(null);

  const { logout } = useAuth();
  const navigate = useNavigate();

  function refetchAll() {
    setLoadError(null);
    Promise.all([fetchCurrentUser().then(setUser), fetchPlaidStatus().then(setPlaidStatus)]).catch(() => {
      setLoadError("Couldn't load your settings. Check your connection and try again.");
    });
  }

  useEffect(() => {
    refetchAll();
  }, []);

  async function handlePasswordSubmit(event: FormEvent) {
    event.preventDefault();
    setPasswordError(null);
    setPasswordSuccess(false);
    if (newPassword !== confirmPassword) {
      setPasswordError("Passwords don't match.");
      return;
    }
    setSavingPassword(true);
    try {
      await updatePassword(newPassword);
      setPasswordSuccess(true);
      setNewPassword("");
      setConfirmPassword("");
    } catch (err) {
      if (axios.isAxiosError(err) && err.response?.status === 400) {
        const detail = err.response.data?.detail;
        const reason = typeof detail === "object" ? detail?.reason : null;
        setPasswordError(reason ?? "That password isn't allowed. Please choose another.");
      } else {
        setPasswordError("Something went wrong. Check your connection and try again.");
      }
    } finally {
      setSavingPassword(false);
    }
  }

  async function handleDisconnect() {
    setDisconnecting(true);
    setDisconnectError(null);
    try {
      await disconnectPlaidAccount();
      navigate("/");
    } catch {
      setDisconnectError("Couldn't disconnect your account. Please try again.");
      setDisconnecting(false);
    }
  }

  async function handleDelete() {
    setDeleting(true);
    setDeleteError(null);
    try {
      await deleteAccount();
      logout();
      navigate("/register");
    } catch {
      setDeleteError("Couldn't delete your account. Please try again.");
      setDeleting(false);
    }
  }

  if (loadError) {
    return (
      <div className="flex flex-col items-center gap-4 py-24 text-center">
        <p className="text-body font-sans text-rust">{loadError}</p>
        <PrimaryButton onClick={refetchAll}>Try again</PrimaryButton>
      </div>
    );
  }

  if (user === null || plaidStatus === null) {
    return null;
  }

  const canDelete = deleteConfirmEmail.trim().toLowerCase() === user.email.toLowerCase();

  return (
    <div className="flex flex-col gap-10">
      <div>
        <h1 className="text-heading font-serif font-medium text-ink">Settings</h1>
        <p className="mt-1 text-body-sm font-sans text-slate">
          Manage your profile, connected account, and data.
        </p>
      </div>

      <div className="rounded-card border border-hairline bg-surface p-6">
        <h2 className="text-heading-sm font-serif font-medium text-ink">Profile</h2>
        <p className="mt-3 text-body-sm font-sans text-slate">{user.email}</p>

        <form className="mt-6 flex max-w-sm flex-col gap-4" onSubmit={handlePasswordSubmit}>
          <TextField
            label="New password"
            type="password"
            value={newPassword}
            onChange={(e) => setNewPassword(e.target.value)}
            required
            minLength={8}
          />
          <TextField
            label="Confirm new password"
            type="password"
            value={confirmPassword}
            onChange={(e) => setConfirmPassword(e.target.value)}
            required
            minLength={8}
          />
          {passwordError && <p className="text-body-sm font-sans text-rust">{passwordError}</p>}
          {passwordSuccess && <p className="text-body-sm font-sans text-slate">Password updated.</p>}
          <PrimaryButton type="submit" disabled={savingPassword} className="w-fit disabled:opacity-60">
            {savingPassword ? "Saving…" : "Change password"}
          </PrimaryButton>
        </form>
      </div>

      <div className="rounded-card border border-hairline bg-surface p-6">
        <h2 className="text-heading-sm font-serif font-medium text-ink">Connected account</h2>
        {plaidStatus.connected ? (
          <>
            <p className="mt-3 text-body-sm font-sans text-slate">
              Connected · linked {new Date(plaidStatus.linked_at as string).toLocaleDateString()}
            </p>
            {disconnectError && <p className="mt-3 text-body-sm font-sans text-rust">{disconnectError}</p>}
            <div className="mt-4">
              <PrimaryButton onClick={handleDisconnect} disabled={disconnecting} className="disabled:opacity-60">
                {disconnecting ? "Disconnecting…" : "Disconnect account"}
              </PrimaryButton>
            </div>
          </>
        ) : (
          <p className="mt-3 text-body-sm font-sans text-slate">Not connected.</p>
        )}
      </div>

      <div className="rounded-card border border-rust p-6">
        <h2 className="text-heading-sm font-serif font-medium text-rust">Danger zone</h2>
        <p className="mt-3 text-body-sm font-sans text-slate">
          Deleting your account permanently removes your profile, connected account, and transaction history.
          Type your email ({user.email}) to confirm.
        </p>
        <div className="mt-4 flex max-w-sm flex-col gap-4">
          <TextField
            label="Confirm email"
            value={deleteConfirmEmail}
            onChange={(e) => setDeleteConfirmEmail(e.target.value)}
          />
          {deleteError && <p className="text-body-sm font-sans text-rust">{deleteError}</p>}
          <PrimaryButton
            onClick={handleDelete}
            disabled={!canDelete || deleting}
            className="w-fit disabled:opacity-60"
          >
            {deleting ? "Deleting…" : "Delete account"}
          </PrimaryButton>
        </div>
      </div>
    </div>
  );
}

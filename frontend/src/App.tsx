import type { ReactNode } from "react";
import { Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { LiveStatusIndicator } from "./components/LiveStatusIndicator";
import { ProtectedRoute } from "./components/ProtectedRoute";
import { SidebarNavItem } from "./components/SidebarNavItem";
import { AlertSocketProvider, useAlertSocketContext } from "./contexts/AlertSocketContext";
import { useAuth } from "./contexts/AuthContext";
import { Dashboard } from "./pages/Dashboard";
import { History } from "./pages/History";
import { Login } from "./pages/Login";
import { Register } from "./pages/Register";
import { Settings } from "./pages/Settings";
import { SubscriptionDetail } from "./pages/SubscriptionDetail";
import { Subscriptions } from "./pages/Subscriptions";

function ShellContent({ children }: { children: ReactNode }) {
  const location = useLocation();
  const navigate = useNavigate();
  const { logout } = useAuth();
  const { status: socketStatus } = useAlertSocketContext();

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 shrink-0 flex-col bg-signal-blue p-6">
        <p className="text-heading-sm font-serif font-medium text-white">Driftline</p>
        <div className="mt-2">
          <LiveStatusIndicator status={socketStatus} />
        </div>
        <nav className="mt-8 flex flex-col gap-1">
          <SidebarNavItem label="Dashboard" active={location.pathname === "/"} onClick={() => navigate("/")} />
          <SidebarNavItem
            label="Subscriptions"
            active={location.pathname.startsWith("/subscriptions")}
            onClick={() => navigate("/subscriptions")}
          />
          <SidebarNavItem
            label="History"
            active={location.pathname === "/history"}
            onClick={() => navigate("/history")}
          />
          <SidebarNavItem
            label="Settings"
            active={location.pathname === "/settings"}
            onClick={() => navigate("/settings")}
          />
        </nav>
        <button
          onClick={logout}
          className="mt-auto text-left text-caption font-sans text-white/60 hover:text-white"
        >
          Log out
        </button>
      </aside>

      <main className="flex-1 px-6 py-10">
        <div className="mx-auto max-w-[1040px]">{children}</div>
      </main>
    </div>
  );
}

function Shell({ children }: { children: ReactNode }) {
  const { token } = useAuth();
  return (
    <AlertSocketProvider token={token}>
      <ShellContent>{children}</ShellContent>
    </AlertSocketProvider>
  );
}

function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Shell>
              <Dashboard />
            </Shell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/subscriptions"
        element={
          <ProtectedRoute>
            <Shell>
              <Subscriptions />
            </Shell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/subscriptions/:id"
        element={
          <ProtectedRoute>
            <Shell>
              <SubscriptionDetail />
            </Shell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/history"
        element={
          <ProtectedRoute>
            <Shell>
              <History />
            </Shell>
          </ProtectedRoute>
        }
      />
      <Route
        path="/settings"
        element={
          <ProtectedRoute>
            <Shell>
              <Settings />
            </Shell>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

export default App;

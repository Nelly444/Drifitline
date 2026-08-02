import { Route, Routes, useLocation, useNavigate } from "react-router-dom";
import { LiveStatusIndicator } from "./components/LiveStatusIndicator";
import { SidebarNavItem } from "./components/SidebarNavItem";
import { useAlertSocket } from "./hooks/useAlertSocket";
import { Dashboard } from "./pages/Dashboard";
import { History } from "./pages/History";

function App() {
  const location = useLocation();
  const navigate = useNavigate();
  const socketStatus = useAlertSocket(() => {});

  return (
    <div className="flex min-h-screen">
      <aside className="w-60 shrink-0 bg-signal-blue p-6">
        <p className="text-heading-sm font-serif font-medium text-white">Driftline</p>
        <div className="mt-2">
          <LiveStatusIndicator status={socketStatus} />
        </div>
        <nav className="mt-8 flex flex-col gap-1">
          <SidebarNavItem label="Dashboard" active={location.pathname === "/"} onClick={() => navigate("/")} />
          <SidebarNavItem
            label="History"
            active={location.pathname === "/history"}
            onClick={() => navigate("/history")}
          />
        </nav>
      </aside>

      <main className="flex-1 px-6 py-10">
        <div className="mx-auto max-w-[1040px]">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/history" element={<History />} />
          </Routes>
        </div>
      </main>
    </div>
  );
}

export default App;

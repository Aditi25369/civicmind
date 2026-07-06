import { useState, useEffect } from "react";
import Dashboard from "./pages/Dashboard";
import ChatPage from "./pages/ChatPage";
import DomainPage from "./pages/DomainPage";
import AlertsPage from "./pages/AlertsPage";
import Sidebar from "./components/Sidebar";
import "./App.css";

export default function App() {
    const [page, setPage] = useState("dashboard");
    const [domain, setDomain] = useState("general");
    const [alerts, setAlerts] = useState([]);

    useEffect(() => {
        fetchAlerts();
        const id = setInterval(fetchAlerts, 30000);
        return () => clearInterval(id);
    }, []);

    async function fetchAlerts() {
        try {
            const res = await fetch(`${import.meta.env.VITE_API_URL || "http://localhost:8080"}/alerts?limit=5`);
            if (res.ok) {
                const data = await res.json();
                setAlerts(data.alerts || []);
            }
        } catch (e) { }
    }

    function navigate(p, d = null) {
        setPage(p);
        if (d) setDomain(d);
    }

    const unresolved = alerts.filter((a) => !a.resolved).length;

    return (
        <div className="app">
            <Sidebar current={page} domain={domain} alertCount={unresolved} onNavigate={navigate} />
            <main className="main-content">
                {page === "dashboard" && <Dashboard onNavigate={navigate} alerts={alerts} />}
                {page === "chat" && <ChatPage domain={domain} />}
                {page === "domain" && <DomainPage domain={domain} />}
                {page === "alerts" && <AlertsPage alerts={alerts} onRefresh={fetchAlerts} />}
            </main>
        </div>
    );
}
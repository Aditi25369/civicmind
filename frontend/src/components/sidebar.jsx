const DOMAINS = [
    { id: "transport", label: "Transport", icon: "🚌" },
    { id: "health", label: "Health", icon: "🏥" },
    { id: "education", label: "Education", icon: "📚" },
    { id: "community", label: "Community", icon: "🏙️" },
];

export default function Sidebar({ current, domain, alertCount, onNavigate }) {
    return (
        <aside className="sidebar">
            <div className="sidebar-brand">
                <span className="brand-icon">⬡</span>
                <span className="brand-name">CivicMind</span>
            </div>

            <nav className="sidebar-nav">
                <button
                    className={`nav-item ${current === "dashboard" ? "active" : ""}`}
                    onClick={() => onNavigate("dashboard")}
                >
                    <span className="nav-icon">▦</span>
                    Dashboard
                </button>

                <button
                    className={`nav-item ${current === "chat" ? "active" : ""}`}
                    onClick={() => onNavigate("chat", "general")}
                >
                    <span className="nav-icon">◈</span>
                    AI Chat
                </button>

                <div className="nav-section-label">Domains</div>

                {DOMAINS.map((d) => (
                    <button
                        key={d.id}
                        className={`nav-item nav-domain ${current === "domain" && domain === d.id ? "active" : ""
                            }`}
                        onClick={() => onNavigate("domain", d.id)}
                    >
                        <span className="nav-icon">{d.icon}</span>
                        {d.label}
                    </button>
                ))}

                <button
                    className={`nav-item ${current === "alerts" ? "active" : ""}`}
                    onClick={() => onNavigate("alerts")}
                >
                    <span className="nav-icon">◉</span>
                    Alerts
                    {alertCount > 0 && (
                        <span className="alert-badge">{alertCount}</span>
                    )}
                </button>
            </nav>

            <div className="sidebar-footer">
                <div className="powered-by">Powered by Vertex AI + Gemini</div>
            </div>
        </aside>
    );
}
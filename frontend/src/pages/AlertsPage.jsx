import { api } from "../services/api";

const SEVERITY_COLOR = {
    low: "#1D9E75", medium: "#BA7517", high: "#D85A30", critical: "#E24B4A",
};

export default function AlertsPage({ alerts, onRefresh }) {
    async function resolve(id) {
        try {
            await api.patch(`/alerts/${id}/resolve`);
            onRefresh();
        } catch (e) {
            console.error(e);
        }
    }

    const active = alerts.filter((a) => !a.resolved);
    const resolved = alerts.filter((a) => a.resolved);

    return (
        <div className="page">
            <div className="page-header">
                <h1>Alerts & Anomalies</h1>
                <button className="btn-secondary" onClick={onRefresh}>Refresh</button>
            </div>

            {active.length === 0 && (
                <div className="no-alerts-banner">All clear — no active alerts</div>
            )}

            {active.length > 0 && (
                <div className="alerts-section">
                    <div className="alerts-section-title">Active ({active.length})</div>
                    {active.map((a) => (
                        <div
                            key={a.id}
                            className="alert-row"
                            style={{ borderLeft: `4px solid ${SEVERITY_COLOR[a.severity] || "#888"}` }}
                        >
                            <div className="alert-row-body">
                                <div className="alert-row-title">{a.title}</div>
                                <div className="alert-row-desc">{a.description}</div>
                                <div className="alert-row-meta">
                                    {a.domain} · {a.severity} · {new Date(a.created_at).toLocaleString()}
                                </div>
                            </div>
                            <button className="btn-resolve" onClick={() => resolve(a.id)}>Resolve</button>
                        </div>
                    ))}
                </div>
            )}

            {resolved.length > 0 && (
                <div className="alerts-section alerts-section--resolved">
                    <div className="alerts-section-title">Resolved ({resolved.length})</div>
                    {resolved.map((a) => (
                        <div key={a.id} className="alert-row alert-row--resolved">
                            <div className="alert-row-body">
                                <div className="alert-row-title">{a.title}</div>
                                <div className="alert-row-meta">
                                    {a.domain} · {new Date(a.created_at).toLocaleString()}
                                </div>
                            </div>
                            <span className="badge-resolved">Resolved</span>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
}
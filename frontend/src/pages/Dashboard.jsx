import { useState, useEffect } from "react";
import {
    LineChart, Line, AreaChart, Area,
    XAxis, YAxis, CartesianGrid, Tooltip,
    ResponsiveContainer, BarChart, Bar, Legend,
} from "recharts";
import { api } from "../services/api";

const DOMAIN_CONFIG = {
    transport: { color: "#1D9E75", label: "Transport", metric: "delay_minutes", unit: "min delay" },
    health: { color: "#D85A30", label: "Health", metric: "utilization_rate", unit: "% utilization" },
    education: { color: "#534AB7", label: "Education", metric: "enrollment_change_pct", unit: "% change" },
    community: { color: "#BA7517", label: "Community", metric: "sentiment_score", unit: "sentiment" },
};

function KpiCard({ domain, config, onNavigate }) {
    const [insight, setInsight] = useState(null);

    useEffect(() => {
        api.post("/insights", { domain, time_range_days: 7, limit: 1 })
            .then((d) => setInsight(d.insights?.[0] || null))
            .catch(() => { });
    }, [domain]);

    return (
        <div
            className="kpi-card"
            style={{ borderTop: `3px solid ${config.color}` }}
            onClick={() => onNavigate("domain", domain)}
        >
            <div className="kpi-domain">{config.label}</div>
            {insight ? (
                <>
                    <div className="kpi-title">{insight.title}</div>
                    <div className={`kpi-severity kpi-severity--${insight.severity}`}>
                        {insight.severity}
                    </div>
                    {insight.value != null && (
                        <div className="kpi-value">
                            {insight.value.toFixed(1)}
                            <span className="kpi-unit"> {config.unit}</span>
                        </div>
                    )}
                    {insight.trend && (
                        <div className={`kpi-trend kpi-trend--${insight.trend}`}>
                            {insight.trend === "up" ? "↑" : insight.trend === "down" ? "↓" : "→"} {insight.trend}
                        </div>
                    )}
                </>
            ) : (
                <div className="kpi-loading">Loading insights…</div>
            )}
        </div>
    );
}

export default function Dashboard({ onNavigate, alerts }) {
    const [forecastData, setForecastData] = useState([]);
    const [loadingForecast, setLoadingForecast] = useState(true);

    useEffect(() => {
        Promise.all(
            ["transport", "health"].map((domain) =>
                api.post("/forecast", { domain, metric: DOMAIN_CONFIG[domain].metric, horizon_days: 7 })
                    .then((d) => ({ domain, points: d.forecast }))
                    .catch(() => ({ domain, points: [] }))
            )
        ).then((results) => {
            const merged = {};
            results.forEach(({ domain, points }) => {
                points.forEach((p) => {
                    if (!merged[p.date]) merged[p.date] = { date: p.date };
                    merged[p.date][domain] = p.value;
                });
            });
            setForecastData(Object.values(merged).sort((a, b) => a.date.localeCompare(b.date)));
            setLoadingForecast(false);
        });
    }, []);

    const recentAlerts = (alerts || []).filter((a) => !a.resolved).slice(0, 3);

    return (
        <div className="page">
            <div className="page-header">
                <h1>Decision Intelligence Dashboard</h1>
                <p className="page-subtitle">Real-time city intelligence powered by Vertex AI + Gemini</p>
            </div>

            <div className="kpi-grid">
                {Object.entries(DOMAIN_CONFIG).map(([domain, config]) => (
                    <KpiCard key={domain} domain={domain} config={config} onNavigate={onNavigate} />
                ))}
            </div>

            <div className="charts-row">
                <div className="chart-card">
                    <div className="chart-title">7-day forecast — transport & health</div>
                    {loadingForecast ? (
                        <div className="chart-loading">Generating forecast with Vertex AI…</div>
                    ) : (
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={forecastData}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                                <YAxis tick={{ fontSize: 11 }} />
                                <Tooltip />
                                <Legend />
                                <Area type="monotone" dataKey="transport" stroke="#1D9E75" fill="#1D9E7522" name="Transport delay" />
                                <Area type="monotone" dataKey="health" stroke="#D85A30" fill="#D85A3022" name="Health utilization" />
                            </AreaChart>
                        </ResponsiveContainer>
                    )}
                </div>

                <div className="chart-card alerts-panel">
                    <div className="chart-title">Active alerts</div>
                    {recentAlerts.length === 0 ? (
                        <div className="no-alerts">No unresolved alerts</div>
                    ) : (
                        recentAlerts.map((a) => (
                            <div key={a.id} className={`alert-item alert-item--${a.severity}`}>
                                <div className="alert-item-title">{a.title}</div>
                                <div className="alert-item-domain">{a.domain} · {a.severity}</div>
                            </div>
                        ))
                    )}
                    <button className="btn-link" onClick={() => onNavigate("alerts")}>
                        View all alerts →
                    </button>
                </div>
            </div>

            <div className="quick-actions">
                <div className="quick-actions-title">Quick analysis</div>
                <div className="quick-actions-grid">
                    {[
                        { label: "Ask about traffic congestion today", domain: "transport" },
                        { label: "Summarize clinic utilization this week", domain: "health" },
                        { label: "Show enrollment trends for this quarter", domain: "education" },
                        { label: "Analyze recent citizen feedback sentiment", domain: "community" },
                    ].map((q) => (
                        <button
                            key={q.label}
                            className="quick-action-btn"
                            onClick={() => onNavigate("chat", q.domain)}
                        >
                            {q.label}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
}
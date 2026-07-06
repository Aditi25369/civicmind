import { useState, useEffect } from "react";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from "recharts";
import { api } from "../services/api";

const DOMAIN_META = {
    transport: {
        color: "#1D9E75", label: "Transport & Mobility",
        metrics: ["delay_minutes", "passenger_count", "on_time_rate"],
        description: "Monitor transit performance, traffic flow, and infrastructure health",
    },
    health: {
        color: "#D85A30", label: "Healthcare & Well-being",
        metrics: ["utilization_rate", "patient_count", "wait_time_minutes"],
        description: "Track clinic utilization, community health trends, and wellness indicators",
    },
    education: {
        color: "#534AB7", label: "Education & Economic Development",
        metrics: ["enrollment_change_pct", "new_enrollments", "completion_rate"],
        description: "Analyze enrollment, workforce development, and learning outcomes",
    },
    community: {
        color: "#BA7517", label: "Community Intelligence",
        metrics: ["sentiment_score", "engagement_rate", "response_count"],
        description: "Understand citizen feedback, service accessibility, and community engagement",
    },
};

const SEVERITY_COLOR = { info: "#1D9E75", warning: "#BA7517", critical: "#D85A30" };

export default function DomainPage({ domain }) {
    const meta = DOMAIN_META[domain] || DOMAIN_META.transport;
    const [insights, setInsights] = useState([]);
    const [forecast, setForecast] = useState([]);
    const [summary, setSummary] = useState("");
    const [loading, setLoading] = useState(true);
    const [metric, setMetric] = useState(meta.metrics[0]);

    useEffect(() => {
        const m = DOMAIN_META[domain] || DOMAIN_META.transport;
        setMetric(m.metrics[0]);
        loadAll(domain, m.metrics[0]);
    }, [domain]);

    async function loadAll(d, m) {
        setLoading(true);
        try {
            const [insRes, fcRes] = await Promise.all([
                api.post("/insights", { domain: d, time_range_days: 30, limit: 4 }),
                api.post("/forecast", { domain: d, metric: m, horizon_days: 14 }),
            ]);
            setInsights(insRes.insights || []);
            setSummary(insRes.summary || "");
            setForecast(fcRes.forecast || []);
        } catch (e) {
            console.error(e);
        } finally {
            setLoading(false);
        }
    }

    async function changeMetric(m) {
        setMetric(m);
        try {
            const fcRes = await api.post("/forecast", { domain, metric: m, horizon_days: 14 });
            setForecast(fcRes.forecast || []);
        } catch (e) { }
    }

    return (
        <div className="page">
            <div className="page-header" style={{ borderLeft: `4px solid ${meta.color}`, paddingLeft: 16 }}>
                <h1>{meta.label}</h1>
                <p className="page-subtitle">{meta.description}</p>
            </div>

            {summary && (
                <div className="summary-card" style={{ borderLeft: `3px solid ${meta.color}` }}>
                    <strong>AI Executive Summary</strong>
                    <p>{summary}</p>
                </div>
            )}

            <div className="domain-grid">
                <div className="chart-card domain-chart">
                    <div className="chart-header">
                        <div className="chart-title">14-day forecast</div>
                        <select className="metric-select" value={metric} onChange={(e) => changeMetric(e.target.value)}>
                            {meta.metrics.map((m) => (
                                <option key={m} value={m}>{m.replace(/_/g, " ")}</option>
                            ))}
                        </select>
                    </div>
                    {loading ? (
                        <div className="chart-loading">Generating with Vertex AI…</div>
                    ) : (
                        <ResponsiveContainer width="100%" height={220}>
                            <AreaChart data={forecast}>
                                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                                <XAxis dataKey="date" tick={{ fontSize: 11 }} tickFormatter={(v) => v.slice(5)} />
                                <YAxis tick={{ fontSize: 11 }} />
                                <Tooltip />
                                <Area type="monotone" dataKey="upper_bound" stroke="none" fill={`${meta.color}22`} name="Upper bound" />
                                <Area type="monotone" dataKey="value" stroke={meta.color} fill={`${meta.color}11`} strokeWidth={2} name={metric.replace(/_/g, " ")} />
                                <Area type="monotone" dataKey="lower_bound" stroke="none" fill="transparent" name="Lower bound" />
                            </AreaChart>
                        </ResponsiveContainer>
                    )}
                </div>

                <div className="insights-list">
                    <div className="chart-title">AI Insights</div>
                    {loading ? (
                        <div className="chart-loading">Analyzing with Gemini…</div>
                    ) : insights.length === 0 ? (
                        <div className="no-data">No insights yet. Seed data first.</div>
                    ) : (
                        insights.map((ins, i) => (
                            <div key={i} className="insight-card" style={{ borderLeft: `3px solid ${SEVERITY_COLOR[ins.severity] || "#888"}` }}>
                                <div className="insight-header">
                                    <span className="insight-title">{ins.title}</span>
                                    <span className="insight-badge" style={{ background: `${SEVERITY_COLOR[ins.severity]}22`, color: SEVERITY_COLOR[ins.severity] }}>
                                        {ins.severity}
                                    </span>
                                </div>
                                <p className="insight-desc">{ins.description}</p>
                                {ins.value != null && (
                                    <div className="insight-metric">
                                        {ins.metric}: <strong>{ins.value.toFixed(1)}</strong>
                                        {ins.trend && (
                                            <span className={`trend-tag trend-tag--${ins.trend}`}>
                                                {ins.trend === "up" ? " ↑" : ins.trend === "down" ? " ↓" : " →"}
                                            </span>
                                        )}
                                    </div>
                                )}
                            </div>
                        ))
                    )}
                </div>
            </div>
        </div>
    );
}
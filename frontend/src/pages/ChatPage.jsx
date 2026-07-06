import { useState, useRef, useEffect } from "react";
import { api } from "../services/api";

const DOMAIN_STARTERS = {
    transport: [
        "What routes have the highest delays this week?",
        "Predict peak congestion times for next Monday",
        "Which bus stops need infrastructure upgrades?",
    ],
    health: [
        "Which clinics have the highest utilization rate?",
        "Are there any disease outbreak patterns in the data?",
        "Recommend healthcare access improvements for underserved zones",
    ],
    education: [
        "What are the enrollment trends for the last quarter?",
        "Which schools need additional resource allocation?",
        "Forecast graduation rates for next year",
    ],
    community: [
        "What are citizens most concerned about this month?",
        "Summarize feedback sentiment across all service categories",
        "Which communities have the lowest engagement scores?",
    ],
    general: [
        "Give me an overview of city performance this week",
        "What are the top 3 issues requiring immediate attention?",
        "How are we performing against last month's benchmarks?",
    ],
};

function MessageBubble({ msg }) {
    const isUser = msg.role === "user";
    return (
        <div className={`message ${isUser ? "message--user" : "message--assistant"}`}>
            <div className="message-avatar">{isUser ? "You" : "AI"}</div>
            <div className="message-body">
                <div className="message-text" style={{ whiteSpace: "pre-wrap" }}>
                    {typeof msg.content === "string" && msg.content.startsWith("{")
                        ? (() => { try { return JSON.parse(msg.content).answer || msg.content; } catch (e) { return msg.content; } })()
                        : msg.content
                    }
                </div>
                {msg.followUps && msg.followUps.length > 0 && (
                    <div className="message-followups">
                        {msg.followUps.map((q, i) => (
                            <span key={i} className="followup-chip" onClick={() => msg.onFollowUp?.(q)}>
                                {q}
                            </span>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
}

export default function ChatPage({ domain }) {
    const [messages, setMessages] = useState([]);
    const [input, setInput] = useState("");
    const [loading, setLoading] = useState(false);
    const [sessionId, setSessionId] = useState(null);
    const [activeDomain, setDomain] = useState(domain || "general");
    const bottomRef = useRef(null);

    useEffect(() => {
        setMessages([]);
        setSessionId(null);
        setDomain(domain || "general");
    }, [domain]);

    useEffect(() => {
        bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }, [messages]);

    async function send(text) {
        const userMsg = text || input.trim();
        if (!userMsg || loading) return;
        setInput("");
        setLoading(true);

        setMessages((prev) => [...prev, { role: "user", content: userMsg }]);

        try {
            const history = messages.slice(-6).map((m) => ({
                role: m.role,
                content: m.content,
            }));

            const data = await api.post("/query", {
                message: userMsg,
                domain: activeDomain,
                session_id: sessionId,
                history,
                use_rag: true,
            });

            if (!sessionId) setSessionId(data.session_id);

            const onFollowUp = (q) => send(q);

            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: data.answer,
                    sources: data.sources,
                    followUps: data.follow_up_questions,
                    onFollowUp,
                },
            ]);
        } catch (err) {
            setMessages((prev) => [
                ...prev,
                {
                    role: "assistant",
                    content: "Sorry, I couldn't connect to the AI service. Please check your API configuration.",
                },
            ]);
        } finally {
            setLoading(false);
        }
    }

    const starters = DOMAIN_STARTERS[activeDomain] || DOMAIN_STARTERS.general;

    return (
        <div className="chat-page">
            <div className="chat-header">
                <div>
                    <h2>AI Analysis — {activeDomain.charAt(0).toUpperCase() + activeDomain.slice(1)}</h2>
                    <p className="chat-subtitle">Gemini 1.5 Pro + Vertex AI Search</p>
                </div>
                <select
                    className="domain-select"
                    value={activeDomain}
                    onChange={(e) => setDomain(e.target.value)}
                >
                    {["general", "transport", "health", "education", "community"].map((d) => (
                        <option key={d} value={d}>{d.charAt(0).toUpperCase() + d.slice(1)}</option>
                    ))}
                </select>
            </div>

            <div className="chat-messages">
                {messages.length === 0 && (
                    <div className="chat-empty">
                        <div className="chat-empty-title">What would you like to analyze?</div>
                        <div className="chat-starters">
                            {starters.map((s, i) => (
                                <button key={i} className="starter-chip" onClick={() => send(s)}>
                                    {s}
                                </button>
                            ))}
                        </div>
                    </div>
                )}

                {messages.map((msg, i) => (
                    <MessageBubble key={i} msg={msg} />
                ))}

                {loading && (
                    <div className="message message--assistant">
                        <div className="message-avatar">AI</div>
                        <div className="message-body">
                            <div className="typing-indicator">
                                <span /><span /><span />
                            </div>
                        </div>
                    </div>
                )}
                <div ref={bottomRef} />
            </div>

            <div className="chat-input-row">
                <textarea
                    className="chat-input"
                    value={input}
                    placeholder={`Ask anything about ${activeDomain} data…`}
                    rows={1}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={(e) => {
                        if (e.key === "Enter" && !e.shiftKey) {
                            e.preventDefault();
                            send();
                        }
                    }}
                />
                <button className="send-btn" onClick={() => send()} disabled={loading || !input.trim()}>
                    Send
                </button>
            </div>
        </div>
    );
}
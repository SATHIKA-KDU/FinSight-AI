import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import date
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from data.db import init_db, get_connection
from agent.agent_core import build_agent, chat

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="FinSight AI",
    page_icon="💎",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Global CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding: 1.5rem 2rem 2rem; }
[data-testid="stSidebar"] {
    background: linear-gradient(160deg, #0f0c29, #302b63, #24243e);
    border-right: 1px solid rgba(255,255,255,0.06);
}
[data-testid="stSidebar"] * { color: #e2e8f0 !important; }
[data-testid="stSidebar"] .stTextInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #fff !important; border-radius: 10px !important;
}
[data-testid="stSidebar"] .stNumberInput input {
    background: rgba(255,255,255,0.08) !important;
    border: 1px solid rgba(255,255,255,0.15) !important;
    color: #fff !important; border-radius: 10px !important;
}
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #667eea22, #764ba222);
    border: 1px solid rgba(102,126,234,0.3);
    border-radius: 16px; padding: 1rem 1.2rem;
    box-shadow: 0 4px 24px rgba(102,126,234,0.08);
}
[data-testid="metric-container"] label {
    color: #94a3b8 !important; font-size: 0.75rem !important;
    font-weight: 500 !important; letter-spacing: 0.08em !important;
    text-transform: uppercase !important;
}
[data-testid="metric-container"] [data-testid="stMetricValue"] {
    font-size: 1.7rem !important; font-weight: 700 !important;
    background: linear-gradient(90deg, #667eea, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    border-bottom: 2px solid rgba(102,126,234,0.15); gap: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    background: transparent; border-radius: 10px 10px 0 0;
    color: #94a3b8 !important; font-weight: 500; font-size: 0.9rem;
    padding: 0.6rem 1.2rem; border: none !important; transition: all 0.2s;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea22, #764ba222) !important;
    color: #a78bfa !important; border-bottom: 2px solid #667eea !important;
}
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important; border: none !important;
    border-radius: 10px !important; font-weight: 600 !important;
    font-size: 0.88rem !important; padding: 0.55rem 1.2rem !important;
    transition: all 0.25s !important; letter-spacing: 0.02em !important;
}
.stButton > button:hover {
    transform: translateY(-1px) !important;
    box-shadow: 0 6px 20px rgba(102,126,234,0.45) !important;
}
[data-testid="stChatMessage"] {
    border-radius: 14px !important; margin-bottom: 0.6rem !important;
    border: 1px solid rgba(102,126,234,0.12) !important;
}
.stProgress > div > div {
    background: linear-gradient(90deg, #667eea, #a78bfa) !important;
    border-radius: 99px !important;
}
.stProgress > div {
    background: rgba(102,126,234,0.15) !important;
    border-radius: 99px !important; height: 10px !important;
}
.section-title {
    font-size: 1.35rem; font-weight: 700;
    background: linear-gradient(90deg, #667eea, #a78bfa);
    -webkit-background-clip: text; -webkit-text-fill-color: transparent;
    margin-bottom: 0.2rem;
}
.section-sub { font-size: 0.82rem; color: #94a3b8; margin-bottom: 1.2rem; }
.info-card {
    background: linear-gradient(135deg, #667eea15, #764ba215);
    border: 1px solid rgba(102,126,234,0.25);
    border-radius: 16px; padding: 1.2rem 1.4rem; margin-bottom: 1rem;
}
.info-card h4 { margin: 0 0 0.3rem; font-size: 0.9rem; font-weight: 600; color: #a78bfa; }
.info-card p { margin: 0; font-size: 0.83rem; color: #94a3b8; line-height: 1.5; }
.hero {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 20px; padding: 2rem 2.4rem; margin-bottom: 1.5rem;
    position: relative; overflow: hidden;
}
.hero h1 { color: white; font-size: 1.6rem; font-weight: 800; margin: 0 0 0.3rem; }
.hero p  { color: rgba(255,255,255,0.75); font-size: 0.9rem; margin: 0; }
.badge { display: inline-block; padding: 2px 10px; border-radius: 99px;
         font-size: 0.72rem; font-weight: 600; letter-spacing: 0.04em; }
.badge-green { background: #064e3b; color: #34d399; }
.badge-yellow { background: #451a03; color: #fbbf24; }
.badge-red { background: #450a0a; color: #f87171; }
hr { border-color: rgba(102,126,234,0.15) !important; }
</style>
""", unsafe_allow_html=True)

# ── Init ───────────────────────────────────────────────────────────────────────
init_db()

if "agent"     not in st.session_state: st.session_state.agent     = None
if "messages"  not in st.session_state: st.session_state.messages  = []
if "api_token" not in st.session_state: st.session_state.api_token = ""

CATEGORY_ICONS = {
    "Food": "🍜", "Transport": "🚌", "Rent": "🏠",
    "Entertainment": "🎮", "Education": "📚", "Health": "💊",
    "Clothing": "👗", "Utilities": "💡", "Other": "📦"
}
CATEGORY_COLORS = {
    "Food": "#667eea", "Transport": "#f59e0b", "Rent": "#10b981",
    "Entertainment": "#ec4899", "Education": "#3b82f6", "Health": "#ef4444",
    "Clothing": "#8b5cf6", "Utilities": "#06b6d4", "Other": "#94a3b8"
}
DEFAULT_BUDGET = {
    "Food": 8000, "Transport": 3000, "Rent": 15000, "Entertainment": 2000,
    "Education": 4000, "Health": 2000, "Clothing": 2000, "Utilities": 3000, "Other": 2000,
}

# ── Sidebar ────────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style="text-align:center;padding:1.2rem 0 0.5rem;">
        <div style="font-size:2.8rem;">💎</div>
        <div style="font-size:1.3rem;font-weight:800;background:linear-gradient(90deg,#667eea,#a78bfa);
             -webkit-background-clip:text;-webkit-text-fill-color:transparent;">FinSight AI</div>
        <div style="font-size:0.75rem;color:#94a3b8;margin-top:2px;">Personal Finance Intelligence</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#a78bfa;letter-spacing:.06em;'>🔑 AGENT SETUP</div>", unsafe_allow_html=True)

    token_input = st.text_input(
        "Groq API Key", type="password",
        value=st.session_state.api_token,
        placeholder="gsk_...",
        help="Get free key at console.groq.com/keys"
    )

    if st.button("⚡ Connect Agent", use_container_width=True):
        if token_input:
            with st.spinner("Initialising FinSight agent..."):
                try:
                    result = build_agent(token_input)
                    st.session_state.agent = result
                    st.session_state.api_token = token_input
                    st.success("✅ Agent connected!")
                except Exception as e:
                    st.error(f"Failed: {e}")
        else:
            st.warning("Please enter your token.")

    agent_status = "🟢 Online" if st.session_state.agent else "🔴 Offline"
    st.markdown(f"<div style='text-align:center;font-size:0.78rem;color:#94a3b8;margin-top:4px;'>Agent status: {agent_status}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<div style='font-size:0.8rem;font-weight:600;color:#a78bfa;letter-spacing:.06em;'>⚡ QUICK ADD EXPENSE</div>", unsafe_allow_html=True)

    with st.form("quick_expense", clear_on_submit=True):
        q_amount = st.number_input("Amount (Rs.)", min_value=1.0, step=50.0, label_visibility="collapsed")
        q_cat = st.selectbox("Category", list(CATEGORY_ICONS.keys()),
                              format_func=lambda x: f"{CATEGORY_ICONS[x]} {x}")
        q_desc = st.text_input("Description", placeholder="What was it for?")
        if st.form_submit_button("➕ Add Expense", use_container_width=True):
            if q_amount > 0:
                conn = get_connection()
                conn.execute("INSERT INTO expenses (date, category, description, amount) VALUES (?,?,?,?)",
                             (date.today().isoformat(), q_cat, q_desc, q_amount))
                conn.commit(); conn.close()
                st.success(f"Added Rs. {q_amount:.0f} · {q_cat}")
                st.rerun()

    st.markdown("---")
    if st.button("🗑 Clear Chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

    st.markdown("""
    <div style='position:fixed;bottom:1rem;left:0;right:0;text-align:center;font-size:0.7rem;color:#475569;'>
        KDU · LB3114 · Intake 41
    </div>""", unsafe_allow_html=True)

# ── Data ───────────────────────────────────────────────────────────────────────
month = date.today().strftime("%Y-%m")
month_label = date.today().strftime("%B %Y")
conn = get_connection()
df = pd.read_sql_query(
    "SELECT date, category, description, amount FROM expenses WHERE date LIKE ? ORDER BY date DESC",
    conn, params=(f"{month}%",))
goals_df = pd.read_sql_query(
    "SELECT id, name, target_amount, saved_amount, deadline FROM goals ORDER BY id DESC", conn)
conn.close()

total_spent = df["amount"].sum() if not df.empty else 0
tx_count = len(df)
top_cat = df.groupby("category")["amount"].sum().idxmax() if not df.empty else "—"
top_cat_icon = CATEGORY_ICONS.get(top_cat, "📦")

# ── Tabs ───────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["💬  Chat Agent", "📊  Dashboard", "🎯  Goals"])

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 1 — CHAT
# ═══════════════════════════════════════════════════════════════════════════════
with tab1:
    st.markdown(f"""
    <div class="hero">
        <h1>💬 FinSight Chat</h1>
        <p>Your AI finance agent · Powered by Llama 3.1 · {month_label}</p>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.agent:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown("""<div class="info-card"><h4>🚀 Getting Started</h4>
                <p>Enter your Groq API key in the sidebar and click <b>Connect Agent</b> to activate FinSight.</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="info-card"><h4>💸 Log Expenses</h4>
                <p>"I spent Rs. 650 on lunch today"<br>"Add Rs. 1200 for transport"</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="info-card"><h4>📊 Budget Analysis</h4>
                <p>"How am I doing this month?"<br>"Which category am I overspending on?"</p></div>""", unsafe_allow_html=True)
        with col2:
            st.markdown("""<div class="info-card"><h4>💡 Savings Tips</h4>
                <p>"Give me savings advice"<br>"How can I save more money?"</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="info-card"><h4>🎯 Goals</h4>
                <p>"Create a goal: save Rs. 50000 for laptop by December"<br>"Show all my goals"</p></div>""", unsafe_allow_html=True)
            st.markdown("""<div class="info-card"><h4>🌐 Free to Use</h4>
                <p>Uses Groq free inference — no credit card needed. Get your key at console.groq.com</p></div>""", unsafe_allow_html=True)
    else:
        if not st.session_state.messages:
            st.markdown("""
            <div style='text-align:center;padding:2rem;color:#94a3b8;'>
                <div style='font-size:2.5rem;margin-bottom:0.5rem;'>💎</div>
                <div style='font-size:1rem;font-weight:600;color:#a78bfa;'>FinSight is ready</div>
                <div style='font-size:0.85rem;margin-top:0.3rem;'>Ask me anything about your finances</div>
            </div>
            """, unsafe_allow_html=True)

        for msg in st.session_state.messages:
            avatar = "💎" if msg["role"] == "assistant" else "👤"
            with st.chat_message(msg["role"], avatar=avatar):
                st.write(msg["content"])

        if user_input := st.chat_input("Ask FinSight about your finances..."):
            st.session_state.messages.append({"role": "user", "content": user_input})
            with st.chat_message("user", avatar="👤"):
                st.write(user_input)
            with st.chat_message("assistant", avatar="💎"):
                with st.spinner("FinSight is thinking..."):
                    try:
                        answer = chat(user_input, st.session_state.agent)
                    except Exception as e:
                        answer = f"I encountered an error: {str(e)}. Please try rephrasing."
                    st.write(answer)
                    st.session_state.messages.append({"role": "assistant", "content": answer})

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 2 — DASHBOARD
# ═══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown(f"""
    <div class="hero">
        <h1>📊 Spending Dashboard</h1>
        <p>{month_label} · {tx_count} transactions recorded</p>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Spent", f"Rs. {total_spent:,.0f}")
    col2.metric("Transactions", tx_count)
    col3.metric("Top Category", f"{top_cat_icon} {top_cat}")
    avg_per_day = total_spent / max(date.today().day, 1)
    col4.metric("Daily Average", f"Rs. {avg_per_day:,.0f}")

    st.markdown("<br>", unsafe_allow_html=True)

    if df.empty:
        st.markdown("""
        <div style='text-align:center;padding:3rem;color:#94a3b8;border:1px dashed rgba(102,126,234,0.3);border-radius:16px;'>
            <div style='font-size:2rem;margin-bottom:0.5rem;'>📭</div>
            <div style='font-weight:600;color:#a78bfa;'>No expenses yet</div>
            <div style='font-size:0.85rem;margin-top:0.3rem;'>Add expenses using the sidebar or chat agent</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        col_a, col_b = st.columns([1, 1.4])
        with col_a:
            st.markdown('<div class="section-title">By Category</div><div class="section-sub">Spending breakdown this month</div>', unsafe_allow_html=True)
            cat_df = df.groupby("category")["amount"].sum().reset_index()
            cat_df["label"] = cat_df.apply(lambda r: f"{CATEGORY_ICONS.get(r['category'],'')} {r['category']}", axis=1)
            colors = [CATEGORY_COLORS.get(c, "#94a3b8") for c in cat_df["category"]]
            fig_donut = go.Figure(go.Pie(
                labels=cat_df["label"], values=cat_df["amount"], hole=0.62,
                marker=dict(colors=colors, line=dict(color="#0f0c29", width=2)),
                textinfo="percent", textfont=dict(size=11, color="white"),
                hovertemplate="<b>%{label}</b><br>Rs. %{value:,.0f}<br>%{percent}<extra></extra>",
            ))
            fig_donut.add_annotation(
                text=f"<b>Rs. {total_spent:,.0f}</b>", x=0.5, y=0.5,
                font=dict(size=13, color="#e2e8f0"), showarrow=False, align="center"
            )
            fig_donut.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), height=300,
                legend=dict(font=dict(color="#94a3b8", size=11), bgcolor="rgba(0,0,0,0)"),
            )
            st.plotly_chart(fig_donut, use_container_width=True)

        with col_b:
            st.markdown('<div class="section-title">Daily Trend</div><div class="section-sub">How your spending changes day by day</div>', unsafe_allow_html=True)
            daily_df = df.groupby("date")["amount"].sum().reset_index()
            daily_df["date"] = pd.to_datetime(daily_df["date"])
            daily_df = daily_df.sort_values("date")
            fig_bar = go.Figure()
            fig_bar.add_trace(go.Bar(
                x=daily_df["date"], y=daily_df["amount"],
                marker=dict(color=daily_df["amount"], colorscale=[[0, "#667eea"], [1, "#a78bfa"]], line=dict(width=0)),
                hovertemplate="<b>%{x|%b %d}</b><br>Rs. %{y:,.0f}<extra></extra>",
            ))
            fig_bar.add_trace(go.Scatter(
                x=daily_df["date"], y=daily_df["amount"].rolling(3, min_periods=1).mean(),
                mode="lines", line=dict(color="#f59e0b", width=2, dash="dot"), name="3-day avg",
            ))
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
                margin=dict(t=10, b=10, l=10, r=10), height=300,
                xaxis=dict(showgrid=False, color="#94a3b8"),
                yaxis=dict(gridcolor="rgba(102,126,234,0.1)", color="#94a3b8", tickprefix="Rs. "),
                showlegend=False, bargap=0.3,
            )
            st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown('<div class="section-title">Budget Health</div><div class="section-sub">How each category compares to monthly limits</div>', unsafe_allow_html=True)
        cat_totals = df.groupby("category")["amount"].sum().to_dict()
        budget_rows = []
        for cat, budget in DEFAULT_BUDGET.items():
            spent = cat_totals.get(cat, 0)
            pct = min((spent / budget) * 100, 100)
            status = "OK" if pct < 80 else ("WARNING" if pct < 100 else "OVER")
            budget_rows.append({"category": cat, "spent": spent, "budget": budget, "pct": pct, "status": status})

        b_cols = st.columns(3)
        for i, row in enumerate(budget_rows):
            with b_cols[i % 3]:
                icon = CATEGORY_ICONS.get(row["category"], "📦")
                color = "#10b981" if row["status"] == "OK" else ("#f59e0b" if row["status"] == "WARNING" else "#ef4444")
                badge_cls = "badge-green" if row["status"] == "OK" else ("badge-yellow" if row["status"] == "WARNING" else "badge-red")
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,#667eea0a,#764ba20a);border:1px solid rgba(102,126,234,0.2);
                     border-radius:14px;padding:1rem 1.1rem;margin-bottom:0.8rem;'>
                    <div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:0.6rem;'>
                        <div style='font-size:0.88rem;font-weight:600;color:#e2e8f0;'>{icon} {row["category"]}</div>
                        <span class='badge {badge_cls}'>{row["status"]}</span>
                    </div>
                    <div style='background:rgba(102,126,234,0.15);border-radius:99px;height:7px;margin-bottom:0.5rem;'>
                        <div style='width:{row["pct"]}%;height:100%;border-radius:99px;
                             background:linear-gradient(90deg,{color}99,{color});'></div>
                    </div>
                    <div style='display:flex;justify-content:space-between;font-size:0.75rem;color:#94a3b8;'>
                        <span>Rs. {row["spent"]:,.0f}</span>
                        <span>{row["pct"]:.0f}% of Rs. {row["budget"]:,}</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        st.markdown('<div class="section-title">Recent Transactions</div>', unsafe_allow_html=True)
        display_df = df.copy()
        display_df["Category"] = display_df["category"].apply(lambda x: f"{CATEGORY_ICONS.get(x,'')} {x}")
        display_df["Amount"] = display_df["amount"].apply(lambda x: f"Rs. {x:,.0f}")
        display_df = display_df.rename(columns={"date": "Date", "description": "Description"})
        st.dataframe(display_df[["Date", "Category", "Description", "Amount"]],
                     use_container_width=True, hide_index=True, height=280)

# ═══════════════════════════════════════════════════════════════════════════════
# TAB 3 — GOALS
# ═══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown(f"""
    <div class="hero">
        <h1>🎯 Savings Goals</h1>
        <p>Track your targets and celebrate milestones</p>
    </div>
    """, unsafe_allow_html=True)

    col_goals, col_form = st.columns([1.6, 1])

    with col_goals:
        if goals_df.empty:
            st.markdown("""
            <div style='text-align:center;padding:3rem;color:#94a3b8;border:1px dashed rgba(167,139,250,0.3);border-radius:16px;'>
                <div style='font-size:2.5rem;margin-bottom:0.5rem;'>🎯</div>
                <div style='font-weight:600;color:#a78bfa;'>No goals yet</div>
                <div style='font-size:0.85rem;margin-top:0.3rem;'>Create your first goal using the form →</div>
            </div>
            """, unsafe_allow_html=True)
        else:
            for _, row in goals_df.iterrows():
                pct = (row["saved_amount"] / row["target_amount"]) * 100 if row["target_amount"] > 0 else 0
                remaining = row["target_amount"] - row["saved_amount"]
                milestone = "🏆" if pct >= 100 else ("🔥" if pct >= 75 else ("💪" if pct >= 50 else ("🌱" if pct >= 25 else "🚀")))
                bar_color = "#10b981" if pct >= 100 else ("#667eea" if pct >= 50 else "#a78bfa")
                st.markdown(f"""
                <div style='background:linear-gradient(135deg,#0f172a,#1e1b4b);border:1px solid rgba(167,139,250,0.25);
                     border-radius:18px;padding:1.4rem;margin-bottom:1rem;'>
                    <div style='display:flex;justify-content:space-between;align-items:flex-start;margin-bottom:0.8rem;'>
                        <div>
                            <div style='font-size:1.05rem;font-weight:700;color:#e2e8f0;'>{milestone} {row["name"]}</div>
                            {"<div style='font-size:0.75rem;color:#94a3b8;margin-top:2px;'>📅 " + str(row["deadline"]) + "</div>" if row["deadline"] else ""}
                        </div>
                        <div style='font-size:2rem;font-weight:800;background:linear-gradient(90deg,#667eea,#a78bfa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;'>{pct:.0f}%</div>
                    </div>
                    <div style='background:rgba(255,255,255,0.08);border-radius:99px;height:10px;margin-bottom:0.8rem;'>
                        <div style='width:{min(pct,100):.1f}%;height:100%;border-radius:99px;background:linear-gradient(90deg,{bar_color}99,{bar_color});'></div>
                    </div>
                    <div style='display:flex;justify-content:space-between;font-size:0.82rem;'>
                        <span style='color:#a78bfa;font-weight:600;'>Rs. {row["saved_amount"]:,.0f} saved</span>
                        <span style='color:#94a3b8;'>Rs. {remaining:,.0f} remaining</span>
                    </div>
                </div>
                """, unsafe_allow_html=True)

            if not goals_df.empty:
                total_target = goals_df["target_amount"].sum()
                total_saved_g = goals_df["saved_amount"].sum()
                overall_pct = (total_saved_g / total_target * 100) if total_target > 0 else 0
                fig_gauge = go.Figure(go.Indicator(
                    mode="gauge+number",
                    value=overall_pct,
                    number={"suffix": "%", "font": {"size": 28, "color": "#a78bfa"}},
                    gauge={
                        "axis": {"range": [0, 100], "tickcolor": "#475569", "tickfont": {"color": "#94a3b8", "size": 10}},
                        "bar": {"color": "#667eea", "thickness": 0.28},
                        "bgcolor": "rgba(0,0,0,0)", "borderwidth": 0,
                        "steps": [
                            {"range": [0, 25],  "color": "rgba(102,126,234,0.08)"},
                            {"range": [25, 50], "color": "rgba(102,126,234,0.13)"},
                            {"range": [50, 75], "color": "rgba(102,126,234,0.18)"},
                            {"range": [75, 100],"color": "rgba(102,126,234,0.24)"},
                        ],
                    },
                    title={"text": "Overall Goals Achievement", "font": {"color": "#94a3b8", "size": 13}},
                ))
                fig_gauge.update_layout(
                    paper_bgcolor="rgba(0,0,0,0)", margin=dict(t=40, b=10, l=30, r=30), height=220,
                    font={"color": "#e2e8f0"},
                )
                st.plotly_chart(fig_gauge, use_container_width=True)

    with col_form:
        st.markdown('<div class="section-title">New Goal</div><div class="section-sub">Set a target and start saving</div>', unsafe_allow_html=True)
        with st.form("add_goal", clear_on_submit=True):
            g_name = st.text_input("Goal name", placeholder="e.g. New laptop")
            g_target = st.number_input("Target amount (Rs.)", min_value=100.0, step=500.0)
            g_deadline = st.date_input("Deadline (optional)", value=None)
            if st.form_submit_button("🎯 Create Goal", use_container_width=True):
                if g_name and g_target > 0:
                    conn = get_connection()
                    conn.execute("INSERT INTO goals (name, target_amount, deadline) VALUES (?,?,?)",
                                 (g_name, g_target, str(g_deadline) if g_deadline else ""))
                    conn.commit(); conn.close()
                    st.success(f"Goal '{g_name}' created!")
                    st.rerun()

        st.markdown("<br>", unsafe_allow_html=True)
        st.markdown('<div class="section-title">Update Progress</div><div class="section-sub">Log money saved toward a goal</div>', unsafe_allow_html=True)
        if not goals_df.empty:
            with st.form("update_goal", clear_on_submit=True):
                goal_names = goals_df["name"].tolist()
                selected_goal = st.selectbox("Select goal", goal_names)
                add_saved = st.number_input("Amount saved (Rs.)", min_value=1.0, step=100.0)
                if st.form_submit_button("💰 Update Savings", use_container_width=True):
                    conn = get_connection()
                    conn.execute("UPDATE goals SET saved_amount = saved_amount + ? WHERE name = ?",
                                 (add_saved, selected_goal))
                    conn.commit(); conn.close()
                    st.success(f"Added Rs. {add_saved:.0f} to '{selected_goal}'!")
                    st.rerun()
        else:
            st.info("Create a goal first to track progress.")

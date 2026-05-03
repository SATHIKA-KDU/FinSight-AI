import os
import json
from groq import Groq
from datetime import date

# ── These imports are resolved at runtime from the project root ────────────────
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data.db import get_connection, init_db

# ── Global state ───────────────────────────────────────────────────────────────
_chat_history = []

DEFAULT_BUDGET = {
    "Food": 8000, "Transport": 3000, "Rent": 15000,
    "Entertainment": 2000, "Education": 4000, "Health": 2000,
    "Clothing": 2000, "Utilities": 3000, "Other": 2000,
}

# ── Tools ──────────────────────────────────────────────────────────────────────

def tool_add_expense(text, client):
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": (
            f"Extract expense info from this text. Return ONLY a JSON object with keys: "
            f"amount (number), category (one of: Food, Transport, Rent, Entertainment, "
            f"Education, Health, Clothing, Utilities, Other), description (string).\n"
            f"Text: {text}\nJSON:"
        )}],
        max_tokens=120, temperature=0,
    )
    try:
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        amount = float(data["amount"])
        category = data.get("category", "Other")
        description = data.get("description", "")
        init_db()
        conn = get_connection()
        conn.execute(
            "INSERT INTO expenses (date, category, description, amount) VALUES (?,?,?,?)",
            (date.today().isoformat(), category, description, amount)
        )
        conn.commit()
        conn.close()
        return f"Recorded Rs. {amount:.2f} for {category} ({description})."
    except Exception:
        return "Couldn't extract expense. Try: 'I spent Rs. 500 on food'"


def tool_get_budget():
    init_db()
    month = date.today().strftime("%Y-%m")
    conn = get_connection()
    rows = conn.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category",
        (f"{month}%",)
    ).fetchall()
    conn.close()
    if not rows:
        return "No expenses recorded this month yet."
    report = f"Budget report for {date.today().strftime('%B %Y')}:\n\n"
    total = 0
    alerts = []
    for cat, spent in rows:
        budget = DEFAULT_BUDGET.get(cat, 2000)
        pct = (spent / budget) * 100
        total += spent
        status = "OK" if pct < 80 else ("WARNING" if pct < 100 else "OVER BUDGET")
        report += f"- {cat}: Rs.{spent:,.0f} / {budget:,} ({pct:.0f}%) {status}\n"
        if pct >= 80:
            alerts.append(f"{cat} at {pct:.0f}%")
    report += f"\nTotal spent: Rs.{total:,.0f}"
    if alerts:
        report += f"\nAlerts: {', '.join(alerts)}"
    return report


def tool_get_expenses():
    init_db()
    month = date.today().strftime("%Y-%m")
    conn = get_connection()
    rows = conn.execute(
        "SELECT date, category, description, amount FROM expenses "
        "WHERE date LIKE ? ORDER BY date DESC LIMIT 10",
        (f"{month}%",)
    ).fetchall()
    conn.close()
    if not rows:
        return "No expenses this month yet."
    total = sum(r[3] for r in rows)
    result = f"Recent expenses (Total: Rs.{total:,.0f}):\n\n"
    for d, cat, desc, amt in rows:
        result += f"- [{d}] {cat}: Rs.{amt:,.0f} — {desc}\n"
    return result


def tool_savings_advice():
    init_db()
    month = date.today().strftime("%Y-%m")
    conn = get_connection()
    rows = conn.execute(
        "SELECT category, SUM(amount) FROM expenses WHERE date LIKE ? GROUP BY category",
        (f"{month}%",)
    ).fetchall()
    conn.close()
    if not rows:
        return "No data yet. Add expenses first. Tip: Use the 50/30/20 rule — 50% needs, 30% wants, 20% savings."
    spending = dict(rows)
    total = sum(spending.values())
    tips = ["Personalised savings advice:\n"]
    if spending.get("Food", 0) > 10000:
        tips.append(f"- Food is Rs.{spending['Food']:,.0f} — meal prepping saves Rs.2,000+/month.")
    if spending.get("Entertainment", 0) > 3000:
        tips.append(f"- Entertainment is Rs.{spending['Entertainment']:,.0f} — split streaming subscriptions.")
    if spending.get("Transport", 0) > 5000:
        tips.append(f"- Transport is Rs.{spending['Transport']:,.0f} — a bus pass saves 30-40%.")
    tips.append(f"- Target Rs.{total*0.20:,.0f}/month savings (20% of Rs.{total:,.0f}).")
    tips.append("- Move money to savings the day you receive your allowance.")
    return "\n".join(tips)


def tool_view_goals():
    init_db()
    conn = get_connection()
    rows = conn.execute(
        "SELECT name, target_amount, saved_amount, deadline FROM goals ORDER BY id DESC"
    ).fetchall()
    conn.close()
    if not rows:
        return "No savings goals yet. Create one!"
    result = "Your savings goals:\n\n"
    for name, target, saved, deadline in rows:
        pct = (saved / target * 100) if target > 0 else 0
        emoji = "🏆" if pct >= 100 else ("🔥" if pct >= 75 else ("💪" if pct >= 50 else "🚀"))
        result += f"{emoji} {name}: Rs.{saved:,.0f} / {target:,.0f} ({pct:.0f}%)"
        if deadline:
            result += f" — by {deadline}"
        result += "\n"
    return result


def tool_create_goal(text, client):
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": (
            f"Extract goal info and return ONLY JSON with keys: "
            f"name (string), target (number), deadline (YYYY-MM-DD or empty string).\n"
            f"Text: {text}\nJSON:"
        )}],
        max_tokens=100, temperature=0,
    )
    try:
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        name = data["name"]
        target = float(data["target"])
        deadline = data.get("deadline", "")
        init_db()
        conn = get_connection()
        conn.execute(
            "INSERT INTO goals (name, target_amount, deadline) VALUES (?,?,?)",
            (name, target, deadline)
        )
        conn.commit()
        conn.close()
        return f"Goal created: '{name}' — target Rs.{target:,.0f}" + (f" by {deadline}." if deadline else ".")
    except Exception:
        return "Couldn't parse goal. Try: 'Create a goal to save Rs.50000 for a laptop by December 2026'"


def tool_update_goal(text, client):
    resp = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": (
            f"Extract goal update info and return ONLY JSON with keys: name (string), saved (number).\n"
            f"Text: {text}\nJSON:"
        )}],
        max_tokens=80, temperature=0,
    )
    try:
        raw = resp.choices[0].message.content.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()
        data = json.loads(raw)
        name = data["name"]
        saved = float(data["saved"])
        init_db()
        conn = get_connection()
        conn.execute(
            "UPDATE goals SET saved_amount = saved_amount + ? WHERE name LIKE ?",
            (saved, f"%{name}%")
        )
        conn.commit()
        row = conn.execute(
            "SELECT target_amount, saved_amount FROM goals WHERE name LIKE ?",
            (f"%{name}%",)
        ).fetchone()
        conn.close()
        if row:
            target, total_saved = row
            pct = (total_saved / target) * 100
            return f"Updated! Rs.{total_saved:,.0f} saved of Rs.{target:,.0f} ({pct:.1f}% complete)."
        return "Goal not found."
    except Exception:
        return "Couldn't parse. Try: 'I saved Rs.5000 towards my laptop goal'"


# ── Intent detection ───────────────────────────────────────────────────────────

def detect_intent(text):
    t = text.lower()
    if any(w in t for w in ["spent", "spend", "bought", "paid", "add expense", "cost me", "i spent", "rs."]):
        return "add_expense"
    if any(w in t for w in ["budget", "overspend", "how am i doing", "budget report", "budget analysis"]):
        return "budget"
    if any(w in t for w in ["show expense", "my expense", "list expense", "recent expense", "what did i spend"]):
        return "get_expenses"
    if any(w in t for w in ["saving tip", "save more", "savings advice", "cut back", "how to save", "give me saving"]):
        return "savings"
    if any(w in t for w in ["create goal", "set goal", "new goal", "save for", "saving for"]):
        return "create_goal"
    if any(w in t for w in ["show goal", "my goal", "list goal", "view goal", "all goal", "how close"]):
        return "view_goals"
    if any(w in t for w in ["saved rs", "saved towards", "update goal", "saved toward", "put rs"]):
        return "update_goal"
    return "general"


# ── Main chat function ─────────────────────────────────────────────────────────

def chat(user_input, api_key):
    global _chat_history
    client = Groq(api_key=api_key)
    intent = detect_intent(user_input)

    if intent == "add_expense":
        tool_result = tool_add_expense(user_input, client)
    elif intent == "budget":
        tool_result = tool_get_budget()
    elif intent == "get_expenses":
        tool_result = tool_get_expenses()
    elif intent == "savings":
        tool_result = tool_savings_advice()
    elif intent == "create_goal":
        tool_result = tool_create_goal(user_input, client)
    elif intent == "view_goals":
        tool_result = tool_view_goals()
    elif intent == "update_goal":
        tool_result = tool_update_goal(user_input, client)
    else:
        tool_result = None

    messages = [{
        "role": "system",
        "content": (
            "You are FinSight, a friendly personal finance assistant for Sri Lankan students. "
            "Be concise, warm, and encouraging. Amounts are in Sri Lankan Rupees (Rs.). "
            "If tool data is provided, summarise it nicely. Keep responses under 120 words."
        )
    }]

    for h in _chat_history[-6:]:
        messages.append(h)

    if tool_result:
        messages.append({
            "role": "user",
            "content": f"User said: {user_input}\n\nData: {tool_result}\n\nGive a friendly concise response."
        })
    else:
        messages.append({"role": "user", "content": user_input})

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=messages,
        max_tokens=300,
        temperature=0.4,
    )
    answer = response.choices[0].message.content

    _chat_history.append({"role": "user", "content": user_input})
    _chat_history.append({"role": "assistant", "content": answer})
    if len(_chat_history) > 20:
        _chat_history = _chat_history[-20:]

    return answer


# ── Build agent ────────────────────────────────────────────────────────────────

def build_agent(api_key):
    global _chat_history
    client = Groq(api_key=api_key)
    # Test the key with a minimal call
    client.chat.completions.create(
        model="llama-3.1-8b-instant",
        messages=[{"role": "user", "content": "hi"}],
        max_tokens=5,
    )
    _chat_history = []
    return api_key

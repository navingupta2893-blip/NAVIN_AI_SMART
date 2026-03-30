from flask import Flask, request, jsonify
import json
import os
from openai import OpenAI

app = Flask(__name__)

# ---------- OpenAI Setup ----------
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# ---------- Load JSON ----------
with open("sap_notes_db2.json", "r") as f:
    data = json.load(f)

# ---------- Smart Matching ----------
def find_error_smart(user_input):
    user_input = user_input.lower()

    best_match = None
    max_score = 0

    for item in data:
        score = 0

        for word in item["error"].lower().split("_"):
            if word in user_input:
                score += 2

        for variant in item.get("errorVariants", []):
            if variant.lower() in user_input:
                score += 3

        if item.get("description"):
            for word in item["description"].lower().split():
                if word in user_input:
                    score += 1

        if score > max_score:
            max_score = score
            best_match = item

    return best_match if max_score > 0 else None

# ---------- Severity Emoji ----------
def get_severity_icon(severity):
    if severity == "High":
        return "🔥 HIGH"
    elif severity == "Medium":
        return "⚠️ MEDIUM"
    else:
        return "🟢 LOW"

# ---------- AI Explanation ----------
def generate_ai_explanation(user_input, result):
    try:
        prompt = f"""
You are an SAP expert.

User query: {user_input}

SAP Error: {result.get("error")}
Description: {result.get("description")}
Possible Causes: {result.get("possibleCauses")}
Recommendations: {result.get("Recommendations")}

Explain in simple words:
- What happened
- Why it happened
- What should be done
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception:
        return (
            f"{result.get('description')}\n\n"
            f"Causes: {', '.join(result.get('possibleCauses', []))}\n\n"
            f"Fix: {', '.join(result.get('Recommendations', []))}"
        )

# ---------- API ----------
@app.route("/api/dump", methods=["POST"])
def get_dump():
    try:
        req = request.json
        user_input = req.get("user_input", "").strip()

        if not user_input:
            return jsonify({
                "status": "error",
                "message": "user_input is required"
            })

        result = find_error_smart(user_input)

        if result:
            ai_text = generate_ai_explanation(user_input, result)
            severity = get_severity_icon(result.get("severity"))

            formatted_output = f"""
==================================================
🤖 SAP SMART SUPPORT AGENT
==================================================

📌 ERROR:
{result.get("error")}

🚨 SEVERITY:
{severity}

--------------------------------------------------

🧠 ANALYSIS:
{ai_text}

--------------------------------------------------

📊 DETAILS:
• Description : {result.get("description")}
• Team        : {result.get("ResponsibleTeam")}

--------------------------------------------------

⚠️ POSSIBLE CAUSES:
{chr(10).join(["  • " + c for c in result.get("possibleCauses", [])])}

--------------------------------------------------

✅ RECOMMENDED ACTIONS:
{chr(10).join(["  • " + r for r in result.get("Recommendations", [])])}

--------------------------------------------------

🔧 TRANSACTION CODES:
{", ".join(result.get("transactionCodes", []))}

--------------------------------------------------

📚 SAP NOTES:
{chr(10).join(["  • " + note for note in result.get("sapNotes", [])])}

--------------------------------------------------

📩 READY MAIL (COPY & SEND):

{result.get("mailDraft")}

==================================================
"""

            return jsonify({
                "status": "success",
                "formatted_response": formatted_output
            })

        return jsonify({
            "status": "not_found",
            "message": "No matching SAP error found"
        })

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

from flask import Flask, request, jsonify
import json
import os
from openai import OpenAI

app = Flask(__name__)

# ---------- OpenAI ----------
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

# ---------- Severity ----------
def severity_tag(sev):
    if sev == "High":
        return "HIGH 🔥"
    elif sev == "Medium":
        return "MEDIUM ⚠️"
    else:
        return "LOW 🟢"

# ---------- AI Explanation ----------
def generate_ai_explanation(user_input, result):
    try:
        prompt = f"""
Explain this SAP issue in simple words.

User: {user_input}
Error: {result.get("error")}
Description: {result.get("description")}
Causes: {result.get("possibleCauses")}
Fix: {result.get("Recommendations")}
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.choices[0].message.content.strip()

    except:
        return f"{result.get('description')} | Fix: {', '.join(result.get('Recommendations', []))}"

# ---------- API ----------
@app.route("/api/dump", methods=["POST"])
def get_dump():
    try:
        req = request.json
        user_input = req.get("user_input", "").strip()

        if not user_input:
            return jsonify({"status": "error", "message": "user_input required"})

        result = find_error_smart(user_input)

        if not result:
            return jsonify({"status": "not_found", "message": "No match found"})

        ai_text = generate_ai_explanation(user_input, result)
        sev = severity_tag(result.get("severity"))

        # ---------- BEAUTIFUL FORMATTING ----------
        formatted = f"""
══════════════════════════════════════════
🤖  SAP SMART ASSISTANT
══════════════════════════════════════════

🔴 ERROR        : {result.get("error")}
⚡ SEVERITY     : {sev}

──────────────────────────────────────────

🧠 ANALYSIS:
{ai_text}

──────────────────────────────────────────

📋 DETAILS:
   Description : {result.get("description")}
   Team        : {result.get("ResponsibleTeam")}

──────────────────────────────────────────

⚠️ POSSIBLE CAUSES:
{chr(10).join([f"   • {c}" for c in result.get("possibleCauses", [])])}

──────────────────────────────────────────

✅ RECOMMENDED ACTIONS:
{chr(10).join([f"   • {r}" for r in result.get("Recommendations", [])])}

──────────────────────────────────────────

🔧 TRANSACTION CODES:
   {", ".join(result.get("transactionCodes", []))}

──────────────────────────────────────────

📚 SAP NOTES:
{chr(10).join([f"   • {n}" for n in result.get("sapNotes", [])])}

──────────────────────────────────────────

📩 MAIL DRAFT:
{result.get("mailDraft")}

══════════════════════════════════════════
✔ END OF ANALYSIS
══════════════════════════════════════════
"""

        return jsonify({
            "status": "success",
            "formatted_response": formatted
        })

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})

# ---------- Run ----------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

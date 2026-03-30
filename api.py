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

# ---------- Smart Matching (NO AI dependency) ----------
def find_error_smart(user_input):
    user_input = user_input.lower()

    best_match = None
    max_score = 0

    for item in data:
        score = 0

        # Match words from error name
        for word in item["error"].lower().split("_"):
            if word in user_input:
                score += 2

        # Match full variants
        for variant in item.get("errorVariants", []):
            if variant.lower() in user_input:
                score += 3

        # Match description keywords
        if item.get("description"):
            for word in item["description"].lower().split():
                if word in user_input:
                    score += 1

        if score > max_score:
            max_score = score
            best_match = item

    return best_match if max_score > 0 else None

# ---------- AI Explanation (with fallback) ----------
def generate_ai_explanation(user_input, result):
    try:
        prompt = f"""
You are an SAP expert helping a support engineer.

User query: {user_input}

SAP Error: {result.get("error")}
Description: {result.get("description")}
Possible Causes: {result.get("possibleCauses")}
Recommendations: {result.get("Recommendations")}

Explain clearly:
1. What happened
2. Why it happened
3. What should be done

Keep it simple and practical.
"""

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        # ---------- Fallback (VERY IMPORTANT) ----------
        return f"""
SAP Error: {result.get("error")}

Description:
{result.get("description")}

Possible Causes:
{", ".join(result.get("possibleCauses", []))}

Recommended Actions:
{", ".join(result.get("Recommendations", []))}
"""

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

            return jsonify({
                "status": "success",
                "ai_explanation": ai_text,
                "data": {
                    "error": result.get("error"),
                    "description": result.get("description"),
                    "possibleCauses": result.get("possibleCauses"),
                    "recommendations": result.get("Recommendations"),
                    "sapNotes": result.get("sapNotes"),
                    "transactionCodes": result.get("transactionCodes"),
                    "severity": result.get("severity"),
                    "team": result.get("ResponsibleTeam"),
                    "mailDraft": result.get("mailDraft")
                }
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

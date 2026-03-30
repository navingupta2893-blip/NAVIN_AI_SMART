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

# ---------- Smart Search ----------
def find_error_smart(user_input):
    user_input = user_input.lower()

    # ✅ Step 1: Direct match
    for item in data:
        if (
            user_input in item.get("error", "").lower()
            or any(user_input in v.lower() for v in item.get("errorVariants", []))
        ):
            return item

    # ✅ Step 2: AI match
    try:
        error_list = [item["error"] for item in data]

        prompt = f"""
You are an SAP expert.

User query: {user_input}

From this list of SAP errors:
{error_list}

Return ONLY the exact matching error name from the list.
If nothing matches, return NONE.
"""

        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}]
        )

        ai_match = response.choices[0].message.content.strip()

        for item in data:
            if item["error"] == ai_match:
                return item

    except Exception as e:
        print("AI matching failed:", str(e))

    return None

# ---------- AI Explanation ----------
def generate_ai_explanation(user_input, result):
    try:
        prompt = f"""
You are an SAP expert helping a support engineer.

User query: {user_input}

SAP Error: {result.get("error")}
Description: {result.get("description")}
Possible Causes: {result.get("possibleCauses")}
Recommendations: {result.get("Recommendations")}

Explain clearly in simple terms:
1. What happened
2. Why it happened
3. What should be done

Keep it short and practical.
"""

        response = client.chat.completions.create(
            model="gpt-5.3",
            messages=[{"role": "user", "content": prompt}]
        )

        return response.choices[0].message.content

    except Exception as e:
        return f"AI explanation failed: {str(e)}"

# ---------- API ----------
@app.route("/api/dump", methods=["POST"])
def get_dump():
    try:
        req = request.json
        user_input = req.get("user_input", "")

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

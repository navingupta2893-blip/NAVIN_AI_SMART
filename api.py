from flask import Flask, request, jsonify
import json

app = Flask(__name__)

# ---------- Load JSON ----------
with open("sap_notes_db2.json", "r") as f:
    data = json.load(f)

# ---------- Search Function ----------
def find_error(user_input):
    user_input = user_input.lower()

    for item in data:
        if (
            user_input in item.get("error", "").lower()
            or any(user_input in v.lower() for v in item.get("errorVariants", []))
        ):
            return item
    return None

# ---------- API ----------
@app.route("/api/dump", methods=["POST"])
def get_dump():
    try:
        req = request.json
        user_input = req.get("user_input", "")

        result = find_error(user_input)

        if result:
            return jsonify({
                "status": "success",
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
    app.run(host="0.0.0.0", port=5000, debug=True)
import streamlit as st
import json

# ---------- Load JSON ----------
with open("sap_notes_db2.json", "r") as f:
    data = json.load(f)

# ---------- Search ----------
def find_error(user_input):
    user_input = user_input.lower()

    for item in data:
        if (
            user_input in item.get("error", "").lower()
            or any(user_input in v.lower() for v in item.get("errorVariants", []))
        ):
            return item
    return None

# ---------- UI ----------
st.set_page_config(page_title="SAP AI Assistant", layout="wide")

st.title("🤖 SAP Dump AI Assistant")

query = st.text_input("Enter SAP Error / Dump", placeholder="e.g. DYNPRO_NOT_FOUND")

if query:
    result = find_error(query)

    if result:
        col1, col2 = st.columns(2)

        with col1:
            st.subheader("🚨 Error")
            st.error(result.get("error"))

            st.subheader("📄 Description")
            st.write(result.get("description"))

            st.subheader("🔥 Severity")
            st.warning(result.get("severity"))

            st.subheader("👨‍💻 Responsible Team")
            st.info(result.get("ResponsibleTeam"))

        with col2:
            st.subheader("⚠️ Possible Causes")
            st.write(result.get("possibleCauses"))

            st.subheader("✅ Recommendations")
            st.success(result.get("Recommendations"))

            st.subheader("🧭 Transaction Codes")
            st.write(result.get("transactionCodes"))

        st.subheader("📘 SAP Notes")
        for note in result.get("sapNotes", []):
            st.markdown(f"- {note}")

        st.subheader("✉️ Mail Draft")
        st.code(result.get("mailDraft"))

    else:
        st.error("❌ No matching SAP error found")
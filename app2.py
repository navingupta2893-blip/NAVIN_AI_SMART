import streamlit as st
import json
# import win32com.client as win32

# ---------- Load JSON ----------
with open("sap_notes_db2.json", "r") as file:
    data = json.load(file)

st.title("SAP BASIS Smart Support Agent 🤖")

user_input = st.text_input("Enter SAP Error / Dump Name")

# ---------- Search Logic ----------
if user_input:
    found = False

    for item in data:
        for err in item["errorVariants"]:
            if err.lower() in user_input.lower():

                found = True

                st.header(f"Error: {item['error']}")

                st.subheader("Description")
                st.write(item["description"])

                st.subheader("Possible Causes")
                for c in item["possibleCauses"]:
                    st.write("• " + c)

                st.subheader("Recommendations")
                for r in item["Recommendations"]:
                    st.write("• " + r)

                # -------- NEW SECTION --------
                st.subheader("Recommended SAP Notes")
                for note in item["sapNotes"]:
                    st.write("• " + note)

                st.subheader("Transactions to Check")
                for t in item["transactionCodes"]:
                    st.write("• " + t)

                st.subheader("Responsible Team")
                st.write(item["ResponsibleTeam"])

                st.subheader("Mail Draft")
                st.code(item["mailDraft"])

                break

        if found:
            break

    if not found:
        st.error("No matching SAP error found")

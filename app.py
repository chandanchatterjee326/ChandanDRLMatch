import streamlit as st
import pandas as pd
import os
from agents.rag_engine import SmartRAG
from agents.content_generator import generate_content_and_rule
from agents.content_synthesizer import synthesize_content
from agents.matcher import smart_match
from agents.workflow import build_graph
from utils.file_loader import load_documents
from concurrent.futures import ThreadPoolExecutor
from utils.rule_formatter import format_rule

st.set_page_config(page_title="Rule Matcher", layout="wide")

st.title("🧠 Enterprise Decision Rule Matcher")

# 🔥 SESSION STATE (for folder persistence)
if "last_folder" not in st.session_state:
    st.session_state.last_folder = ""

# ================= LAYOUT =================
col1, col2 = st.columns(2)

# ================= LEFT PANEL =================
with col1:
    st.subheader("📂 Reference Documents")

    folder_input = st.text_input(
        "Enter Document Folder Path (Optional)",
        value=st.session_state.last_folder
    )

    # 🔥 Use previous if empty
    if folder_input:
        st.session_state.last_folder = folder_input

    folder = st.session_state.last_folder

    if folder and os.path.exists(folder):
        st.success(f"Using Folder: {folder}")

        # 🔥 Show file list
        files = os.listdir(folder)
        st.markdown("**📄 Files in Folder:**")
        for f in files:
            st.write(f"• {f}")

    else:
        st.warning("No valid folder selected")

# ================= RIGHT PANEL =================
with col2:
    st.subheader("📊 Input Data")

    file = st.file_uploader("Upload Excel File", type=["xlsx"])

    run_btn = st.button("🚀 Run Matching")

# ================= PROCESS =================
if run_btn and file and folder:

    st.info("⏳ Processing... Please wait")

    df = pd.read_excel(file)
    docs = load_documents(folder)
    rag = SmartRAG(docs)

    graph = build_graph(generate_content_and_rule, synthesize_content, smart_match)

    results = []

    def process(i, row):
        query = " ".join([str(v) for v in row.to_dict().values()])
        chunks = rag.retrieve(query)

        state = {
            "row": row.to_dict(),
            "chunks": chunks
        }

        result = graph.invoke(state)

        match = result["match"]

        # 🔥 SCORE CALCULATION
        details = match.get("details", [])
        total = len(result["rule1"].get("conditions", []))
        matched = total - len(details) if total else 0
        score = round((matched / total) * 100, 2) if total else 0

        return {
            "Row ID": i,
            "Rule 1": format_rule(result["rule1"]),
            "Rule 2": format_rule(result["rule2"]),
            "Flag": match["flag"],
            "Match %": score,
            "Reason": match["reason"],
            "Details": details
        }

    with ThreadPoolExecutor(max_workers=6) as ex:
        results = list(ex.map(lambda x: process(x[0], x[1]), df.iterrows()))

    df_out = pd.DataFrame(results)

    # ================= SUMMARY =================
    st.success("✅ Matching Completed")

    colA, colB, colC = st.columns(3)
    colA.metric("Total Rows", len(df_out))
    colB.metric("Matches", (df_out["Flag"] == "MATCH").sum())
    colC.metric("Mismatches", (df_out["Flag"] == "MISMATCH").sum())

    st.divider()

    # ================= COLOR FUNCTION =================
    def highlight_flag(val):
        if val == "MATCH":
            return "background-color: #d4edda; color: black;"
        else:
            return "background-color: #f8d7da; color: black;"

    # ================= TABLE =================
    st.subheader("📋 Results")

    styled_df = df_out.style.applymap(highlight_flag, subset=["Flag"])

    st.dataframe(styled_df, use_container_width=True)

    # ================= DOWNLOAD =================
    st.download_button(
        "📥 Download Results",
        df_out.to_csv(index=False),
        file_name="rule_matching_output.csv",
        mime="text/csv"
    )

    # ================= DETAILS =================
    st.subheader("🔍 Condition-Level Details")

    for i, row in df_out.iterrows():
        with st.expander(f"Row {row['Row ID']} | {row['Flag']} | {row['Match %']}%"):

            st.markdown("### 🧾 Rule 1")
            st.code(row["Rule 1"])

            st.markdown("### 📄 Rule 2")
            st.code(row["Rule 2"])

            st.markdown("### ⚠️ Reason")
            st.write(row["Reason"])

            st.markdown("### 🔬 Condition Issues")

            if row["Details"]:
                for d in row["Details"]:
                    st.write(f"• {d}")
            else:
                st.success("All conditions matched ✅")

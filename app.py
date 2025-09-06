import streamlit as st
import pandas as pd
import plotly.io as pio
from completed_codebase.final_ans import main_agent  # <-- assuming your code is in main.py

st.set_page_config(page_title="HDB Resale Demo", layout="centered")

st.title("🏠 HDB Resale Prices Demo")

# User input
user_question = st.text_input("Ask a question about HDB resale prices:", 
                              "How has average resale price changed over the years?")

if st.button("Run Agent"):
    with st.spinner("Thinking..."):
        output = main_agent(user_question)

    # Show insights
    # SUBHEADER FOR INSIGHTS #
    st.write(output["insights"].replace("$", r"\$").replace("\\n", "\n"))

    # Show visualisation if available
    if output.get("visualisation"):
        st.subheader("📈 Visualisation")
        with open(output["visualisation"]) as f:
            fig_json = f.read()
        fig = pio.from_json(fig_json)
        # SHOW PLOTLY CHART! https://docs.streamlit.io/develop/api-reference/charts/st.plotly_chart #

    # Show dataframe
    if output["result_df"]:
        df = pd.DataFrame(output["result_df"]["rows"], 
                          columns=output["result_df"]["columns"])
        st.subheader("📊 Data")
        # SHOW DATAFRAME! https://docs.streamlit.io/develop/api-reference/data/st.dataframe #

    
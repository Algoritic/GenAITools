import streamlit as st
import pandas as pd
from evaluator import evaluate_all_questions
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# Streamlit UI
st.title("LLM Evaluation Tool")

# File upload widget
uploaded_file = st.file_uploader("Upload your CSV file", type=["csv"])

if uploaded_file is not None:
    # Load the CSV data
    df = pd.read_csv(uploaded_file, encoding='ISO-8859-1') 

    if st.button("Evaluate"):
        # Perform evaluation
        with st.spinner('Evaluating...'):
            evaluation_results = evaluate_all_questions(df)
            st.success("Evaluation complete!")

        # Display results
        st.write(evaluation_results)

        # Allow downloading the evaluation results as a CSV file
        csv_file = evaluation_results.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Evaluation Results",
            data=csv_file,
            file_name="evaluation_results.csv",
            mime='text/csv'
        )

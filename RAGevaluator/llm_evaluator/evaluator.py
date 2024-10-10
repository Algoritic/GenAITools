import os
import pandas as pd
import time
import random
from langchain_openai import AzureChatOpenAI
from langchain.evaluation import load_evaluator
from concurrent.futures import ThreadPoolExecutor, as_completed
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Set up Azure OpenAI Client
ll_model = AzureChatOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    deployment_name=os.getenv("DEPLOYMENT_NAME"), 
    openai_api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    temperature=0
)

def load_data(file_path):
    """Load the CSV file for evaluation."""
    df = pd.read_csv(file_path, encoding='ISO-8859-1')  
    return df

# def evaluate_answer(question, ground_truth, generated_answer, evaluators, max_retries=5):
#     """Evaluate the generated answer against the ground truth with retry logic for rate limits."""
#     result = {
#         "Question": question,
#         "Ground Truth": ground_truth,
#         "Generated Answer": generated_answer,
#     }

#     for criterion, evaluator in evaluators.items():
#         retry_count = 0
#         success = False

#         while not success and retry_count < max_retries:
#             try:
#                 eval_result = evaluator.evaluate_strings(
#                     input=question,
#                     prediction=generated_answer,
#                     reference=ground_truth
#                 )
#                 result[criterion] = eval_result["score"]
#                 success = True
#             except Exception as e:
#                 print(f"Error encountered during {criterion} evaluation: {e}")
#                 result[criterion] = None
                
#                 if "RateLimitError" in str(e):
#                     # Exponential backoff with jitter
#                     retry_count += 1
#                     backoff_time = (2 ** retry_count) + random.uniform(0, 1)  # Exponential backoff with some randomness
#                     print(f"Rate limit hit. Retrying after {backoff_time:.2f} seconds.")
#                     time.sleep(backoff_time)
#                 else:
#                     break  # If it's not a rate limit error, break out of retry loop

#     return result

def evaluate_answer(question, ground_truth, generated_answer, evaluators, max_retries=5):
    """Evaluate the generated answer against the ground truth with retry logic for rate limits."""
    result = {
        "Question": question,
        "Ground Truth": ground_truth,
        "Generated Answer": generated_answer,
    }

    for criterion, evaluator in evaluators.items():
        retry_count = 0
        success = False

        while not success and retry_count < max_retries:
            try:
                eval_result = evaluator.evaluate_strings(
                    input=question,
                    prediction=generated_answer,
                    reference=ground_truth
                )
                score = eval_result["score"]

                # Convert score to percentage
                percentage_score = score * 100 if score is not None else 0

                # Append the result with a pass/fail indicator
                result[criterion] = {
                    "Percentage Score": f"{percentage_score:.2f}%",
                    "Pass/Fail": "Pass" if percentage_score >= 80 else "Fail"
                }

                success = True
            except Exception as e:
                print(f"Error encountered during {criterion} evaluation: {e}")
                result[criterion] = {
                    "Percentage Score": "0.00%",  # default to 0% on failure
                    "Pass/Fail": "Fail"
                }

                if "RateLimitError" in str(e):
                    # Exponential backoff with jitter
                    retry_count += 1
                    backoff_time = (2 ** retry_count) + random.uniform(0, 1)  # Exponential backoff with some randomness
                    print(f"Rate limit hit. Retrying after {backoff_time:.2f} seconds.")
                    time.sleep(backoff_time)
                else:
                    break  # If it's not a rate limit error, break out of retry loop

    return result

def evaluate_all_questions(df):
    """Evaluate all questions in the DataFrame."""
    questions = df["Question"].tolist()
    ground_truths = df["Ground Truth"].tolist()
    generated_answers = df["Generated Answer"].tolist()

    # Define evaluators for different criteria
    evaluators = {
        "conciseness": load_evaluator("labeled_criteria", criteria="conciseness", llm=ll_model),
        "relevance": load_evaluator("labeled_criteria", criteria="relevance", llm=ll_model),
        "correctness": load_evaluator("labeled_criteria", criteria="correctness", llm=ll_model),
        "coherence": load_evaluator("labeled_criteria", criteria="coherence", llm=ll_model),
        "helpfulness": load_evaluator("labeled_criteria", criteria="helpfulness", llm=ll_model),
        "depth": load_evaluator("labeled_criteria", criteria="depth", llm=ll_model),
        "detail": load_evaluator("labeled_criteria", criteria="detail", llm=ll_model),
        "creativity": load_evaluator("labeled_criteria", criteria="creativity", llm=ll_model),
        "harmfulness": load_evaluator("labeled_criteria", criteria="harmfulness", llm=ll_model),
        "maliciousness": load_evaluator("labeled_criteria", criteria="maliciousness", llm=ll_model),
        "misogyny": load_evaluator("labeled_criteria", criteria="misogyny", llm=ll_model),
        "criminality": load_evaluator("labeled_criteria", criteria="criminality", llm=ll_model),
        "insensitivity": load_evaluator("labeled_criteria", criteria="insensitivity", llm=ll_model),
        "controversiality": load_evaluator("labeled_criteria", criteria="controversiality", llm=ll_model),
    }

    evaluation_results = []

    with ThreadPoolExecutor(max_workers=5) as executor:  # Limit number of threads
        futures = [executor.submit(evaluate_answer, q, gt, ga, evaluators)
                   for q, gt, ga in zip(questions, ground_truths, generated_answers)]
        for future in as_completed(futures):
            result = future.result()
            evaluation_results.append(result)

            # Print the result immediately after it's completed
            print(f"Evaluation result: {result}")  # Print the evaluation result in real time

    return pd.DataFrame(evaluation_results)

def save_results(df, file_name):
    """Save the evaluation results to a CSV file."""
    df.to_csv(file_name, index=False)

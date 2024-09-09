from promptflow.core import tool

def improve_input(latest_output, history):
    
    # Initialize improved input with the latest output
    improved_input = latest_output
    
    # If the latest output is too short or lacks detail, ask for more
    if len(latest_output.split()) < 20:
        improved_input += " Can you provide more details?"
    
    # If the latest output indicates uncertainty, refine the question
    if "I'm not sure" in latest_output or "I don't know" in latest_output:
        improved_input = history[-1]['question'] + " Please clarify or provide additional context."
    
    # You can add more logic here to handle specific cases
    return improved_input

@tool
def feedback_loop_agent(latest_output: str, history: list):
    
    # Improve the input based on the latest output and history
    improved_input = improve_input(latest_output, history)
    
    # Return the improved input as the output
    return {"improved_input": improved_input}

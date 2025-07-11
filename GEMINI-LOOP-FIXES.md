# Proposal: An Externally Controlled DSPy Agent Loop

This document outlines a simplified and improved architecture for an agentic loop that provides full external control while deeply leveraging DSPy's core strengths, particularly its optimization capabilities. This design explicitly avoids `dspy.ReAct` to meet the requirement for an externally managed loop.

## 1. The Core Problem: The Need for a "Glass-Box" Agent

The `simplified-agent-loop.md` document correctly explains `dspy.ReAct`. However, `dspy.ReAct` is an integrated, self-contained module that runs the entire agent loop internally. This "black-box" approach does not allow for:
- Step-by-step execution and inspection.
- Custom logic between agent steps (e.g., complex state management, user-in-the-loop validation).
- External control over termination conditions beyond `max_iters`.

The proposed solution is a **"glass-box" agent**, where the reasoning is handled by a DSPy module, but the loop itself is managed by your application code.

**The flow is as follows:**
1.  **External Controller**: Manages the overall task and history.
2.  **DSPy Reasoner**: Takes the history and generates the next `thought` and `tool_call`.
3.  **External Controller**: Receives the `tool_call`, executes the corresponding tool.
4.  **External Controller**: Appends the `tool_output` to the history and decides whether to loop again or terminate.

## 2. Proposed Implementation

We break the agent into two parts: a simple DSPy `Module` for reasoning and an external Python function for the control loop.

### 2.1. The Reasoning Module

First, we define a `dspy.Signature` that captures a single step of reasoning. It takes the history of interactions and the original question, and produces a new thought and a tool call.

```python
import dspy

class CoT(dspy.Signature):
    """Think step-by-step to plan the next tool call."""
    question = dspy.InputField(desc="The user's original question.")
    history = dspy.InputField(desc="The history of previous tool calls and observations.")
    
    thought = dspy.OutputField(desc="The chain of thought leading to the next action.")
    tool_call = dspy.OutputField(desc="The tool to call, in the format `ToolName(param='value')`.")

class AgentReasoner(dspy.Module):
    """A simple agent reasoner module."""
    def __init__(self):
        super().__init__()
        self.generate_next_step = dspy.Predict(CoT)

    def forward(self, question, history):
        return self.generate_next_step(question=question, history=history)
```

### 2.2. The External Control Loop

The control loop is just a standard Python function. It owns the state (`history`) and calls the `AgentReasoner` to decide the next action.

```python
from your_tool_registry import tool_registry # Assuming you have a tool registry

def run_agent_loop(question: str, reasoner: AgentReasoner, max_steps: int = 5):
    """
    Externally controlled agent loop.
    """
    history = ""
    
    for i in range(max_steps):
        # 1. Reason about the next step
        prediction = reasoner(question=question, history=history)
        thought = prediction.thought
        tool_call_str = prediction.tool_call
        
        print(f"--- Step {i+1} ---")
        print(f"Thought: {thought}")
        print(f"Tool Call: {tool_call_str}")

        # 2. Check for termination
        if "FinalAnswer" in tool_call_str:
            final_answer = tool_registry.execute(tool_call_str)
            print(f"Final Answer: {final_answer}")
            return final_answer

        # 3. Execute the tool (externally)
        # This part requires a robust way to parse the tool_call_str and execute it.
        # For example, using the existing tool registry.
        observation = tool_registry.execute(tool_call_str)
        print(f"Observation: {observation}")
        
        # 4. Update history and loop
        history += f"\nThought: {thought}\nAction: {tool_call_str}\nObservation: {observation}"

    return "Agent stopped due to max steps."

# --- Example Usage ---
# dspy.configure(...)
# reasoner = AgentReasoner()
# run_agent_loop("What is the capital of France and what is the weather there?", reasoner)
```

## 3. Aligning with DSPy Best Practices: Optimization

This "glass-box" approach remains fully compatible with DSPy's optimization. We can compile the `AgentReasoner` module to improve its ability to generate correct and efficient tool calls.

### 3.1. Creating Training Data

First, create `dspy.Example` objects that contain traces of successful agent trajectories. The `history` and `question` are inputs, and the `thought` and `tool_call` are the desired outputs for a single reasoning step.

```python
# Example for the first step
ex1_step1 = dspy.Example(
    question="What is the capital of France?",
    history="",
    thought="I need to find the capital of France. The `search` tool seems appropriate for this.",
    tool_call="search(query='capital of France')"
).with_inputs("question", "history")

# Example for a subsequent step
ex2_step2 = dspy.Example(
    question="What is the capital of France and what is the weather there?",
    history="Thought: I need to find the capital of France. The `search` tool seems appropriate.\nAction: search(query='capital of France')\nObservation: The capital of France is Paris.",
    thought="Now that I know the capital is Paris, I need to find the weather there. The `get_weather` tool is perfect for this.",
    tool_call="get_weather(city='Paris')"
).with_inputs("question", "history")

trainset = [ex1_step1, ex2_step2]
```

### 3.2. Compiling the Reasoner

We can use a teleprompter like `BootstrapFewShot` to optimize our `AgentReasoner`. The metric would evaluate the quality of the predicted `tool_call`.

```python
from dspy.teleprompt import BootstrapFewShot

def validate_tool_call(example, pred, trace=None):
    # A simple metric: was the predicted tool call the same as the gold one?
    return example.tool_call.strip() == pred.tool_call.strip()

# Configure the teleprompter
teleprompter = BootstrapFewShot(metric=validate_tool_call, max_bootstrapped_demos=2)

# Compile the reasoner
optimized_reasoner = teleprompter.compile(AgentReasoner(), trainset=trainset)

# The optimized_reasoner can now be used in the external loop
# run_agent_loop("What is the capital of Germany?", optimized_reasoner)
```

## 4. Summary of Improvements

This approach provides a clear and simple path to achieving an externally controlled agentic loop:

1.  **Full Control**: Your code decides when to reason, when to act, and when to stop.
2.  **Simplicity**: The DSPy part is a very simple `Predict` module, making it easy to understand and debug.
3.  **Leverages DSPy**: We retain the most powerful feature of DSPy—the ability to **optimize** the agent's reasoning process through compilation, turning brittle prompt engineering into a more robust programming workflow.
4.  **Flexibility**: The external loop can easily accommodate complex tool execution logic, error handling, and state management without complicating the DSPy module.
5.  **Testability**: It's easier to unit test the `AgentReasoner` and the control loop logic separately.

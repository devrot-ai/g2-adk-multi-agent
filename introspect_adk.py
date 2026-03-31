import inspect
import importlib

mod = importlib.import_module("google.adk.agents")
Agent = getattr(mod, "Agent", None)
LlmAgent = getattr(mod, "LlmAgent", None)

print("Agent:", Agent.__name__ if Agent else "NOT_FOUND")
if Agent:
    try:
        sigA = inspect.signature(Agent)
    except Exception as e:
        sigA = f"<signature unavailable: {e}>"
    print("Agent signature:", sigA)

    try:
        init_sig = inspect.signature(Agent.__init__)
        sub_params = [p for p in init_sig.parameters if "sub" in p.lower()]
    except Exception as e:
        init_sig = f"<init signature unavailable: {e}>"
        sub_params = []

    print("Agent.__init__ signature:", init_sig)
    print("Agent.__init__ params containing 'sub':", sub_params)

print("LlmAgent:", LlmAgent.__name__ if LlmAgent else "NOT_FOUND")
if LlmAgent:
    try:
        sigL = inspect.signature(LlmAgent)
    except Exception as e:
        sigL = f"<signature unavailable: {e}>"
    print("LlmAgent signature:", sigL)

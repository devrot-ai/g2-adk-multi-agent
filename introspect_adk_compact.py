import inspect

def short(sig, n=800):
    s = str(sig)
    return s if len(s) <= n else s[:n] + '...<truncated>'

from google.adk.agents import Agent
print('Agent:', Agent.__name__)
print('Agent signature:', short(inspect.signature(Agent)))
init_sig = inspect.signature(Agent.__init__)
print('Agent.__init__ signature:', short(init_sig))
print("Agent.__init__ params containing 'sub':", [p for p in init_sig.parameters if 'sub' in p.lower()])

try:
    from google.adk.agents import LlmAgent
    print('LlmAgent:', LlmAgent.__name__)
    print('LlmAgent signature:', short(inspect.signature(LlmAgent)))
except Exception as e:
    print('LlmAgent NOT_AVAILABLE:', e)

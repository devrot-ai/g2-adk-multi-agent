import inspect
from google.adk.runners import Runner
src = inspect.getsource(getattr(Runner,'_validate_runner_params'))
print('=== Runner._validate_runner_params (filtered) ===')
for i,l in enumerate(src.splitlines(),1):
    if any(k in l for k in ['def ', 'app_name', 'agent', 'ValueError', 'app =', 'app.name', 'return']):
        print(f"{i:03d}: {l}")

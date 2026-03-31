import inspect
from google.adk.runners import Runner
for meth in ['run','run_async']:
    src = inspect.getsource(getattr(Runner,meth))
    print(f"\n=== Runner.{meth} (filtered) ===")
    for i,l in enumerate(src.splitlines(),1):
        if any(k in l for k in ['def ', 'session', 'auto_create_session', 'create_session', 'get_session', 'new_message', 'app_name', 'yield', 'ValueError', 'user_id', 'session_id']):
            print(f"{i:03d}: {l}")

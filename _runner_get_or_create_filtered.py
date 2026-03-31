import inspect
from google.adk.runners import Runner
src = inspect.getsource(getattr(Runner,'_get_or_create_session'))
print('=== Runner._get_or_create_session (filtered) ===')
for i,l in enumerate(src.splitlines(),1):
    if any(k in l for k in ['def ', 'session', 'app_name', 'auto_create_session', 'create_session', 'get_session', 'ValueError', 'user_id', 'session_id']):
        print(f"{i:03d}: {l}")

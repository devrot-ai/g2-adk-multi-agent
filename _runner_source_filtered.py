import inspect, re
from google.adk.runners import Runner, InMemoryRunner

for cls, meth in [(InMemoryRunner,'__init__'),(Runner,'__init__'),(Runner,'run_debug')]:
    src = inspect.getsource(getattr(cls,meth))
    print(f"\n=== {cls.__name__}.{meth} (filtered) ===")
    for i,l in enumerate(src.splitlines(),1):
        if any(k in l for k in ['app_name','session_service','auto_create_session','create_session','get_session','InMemorySessionService','agent=', 'def ', 'new_session', 'session_id','user_id','types.UserContent','run_async','new_message']):
            print(f"{i:03d}: {l}")

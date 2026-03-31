import inspect, importlib
from google.adk import runners, sessions
print('InMemoryRunner sig:', inspect.signature(runners.InMemoryRunner))
print('InMemorySessionService sig:', inspect.signature(sessions.InMemorySessionService))
print('Session sig:', inspect.signature(sessions.Session))

for cls_name in ['Runner','InMemoryRunner']:
    cls = getattr(runners, cls_name)
    print(f"\n{cls_name} run_debug doc:\n", inspect.getdoc(getattr(cls,'run_debug')))
    print(f"{cls_name} run doc:\n", inspect.getdoc(getattr(cls,'run')))

from google.genai import types
print('\nContent sig:', inspect.signature(types.Content))
print('UserContent sig:', inspect.signature(types.UserContent))
print('Part sig:', inspect.signature(types.Part))

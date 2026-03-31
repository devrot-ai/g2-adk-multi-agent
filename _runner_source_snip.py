import inspect
from google.adk.runners import InMemoryRunner, Runner

for cls, meth in [(InMemoryRunner,'__init__'),(Runner,'__init__'),(Runner,'run_debug')]:
    print(f"\n=== {cls.__name__}.{meth} ===")
    src = inspect.getsource(getattr(cls,meth))
    lines = src.splitlines()
    for i,l in enumerate(lines[:120],1):
        print(f"{i:03d}: {l}")

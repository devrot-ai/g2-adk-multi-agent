import inspect
import importlib
from pprint import pprint

mods = ['google.adk.runners','google.adk.sessions','google.adk.agents']
for m in mods:
    print(f"\n=== MODULE {m} ===")
    try:
        mod = importlib.import_module(m)
        classes = []
        funcs = []
        for name, obj in inspect.getmembers(mod):
            if name.startswith('_'):
                continue
            if inspect.isclass(obj) and obj.__module__.startswith(m):
                classes.append(name)
            elif inspect.isfunction(obj) and obj.__module__.startswith(m):
                funcs.append(name)
        print('Classes:', classes)
        print('Functions:', funcs)
    except Exception as e:
        print('IMPORT_ERROR:', repr(e))

print('\n=== RUNNER DETAILS ===')
try:
    runners = importlib.import_module('google.adk.runners')
    Runner = getattr(runners, 'Runner', None)
    print('Runner exists:', Runner is not None)
    if Runner is not None:
        print('Runner signature:', inspect.signature(Runner))
        methods = []
        for name, obj in inspect.getmembers(Runner):
            if name.startswith('_'):
                continue
            if inspect.isfunction(obj) or inspect.ismethoddescriptor(obj):
                methods.append(name)
        print('Runner methods:', methods)
        for m in methods:
            if any(k in m.lower() for k in ['run','invoke','stream']):
                try:
                    print(f'  {m}{inspect.signature(getattr(Runner,m))}')
                except Exception as e:
                    print(f'  {m}: signature unavailable ({e})')
except Exception as e:
    print('RUNNER_ERROR:', repr(e))

print('\n=== SEARCH run/invoke-like in module classes ===')
for module_name in mods:
    try:
        mod = importlib.import_module(module_name)
        for cname, cobj in inspect.getmembers(mod, inspect.isclass):
            if not cobj.__module__.startswith(module_name) or cname.startswith('_'):
                continue
            interesting = []
            for n, o in inspect.getmembers(cobj):
                if n.startswith('_'):
                    continue
                if inspect.isfunction(o) or inspect.ismethoddescriptor(o):
                    if any(k in n.lower() for k in ['run','invoke','stream','send','create','get_session','session']):
                        try:
                            sig = str(inspect.signature(o))
                        except Exception:
                            sig = '(?)'
                        interesting.append((n,sig))
            if interesting:
                print(f'{module_name}.{cname}:')
                for n,s in interesting:
                    print(f'  - {n}{s}')
    except Exception as e:
        print(module_name, 'error', e)

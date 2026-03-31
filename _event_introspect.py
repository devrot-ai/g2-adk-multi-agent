import inspect
from google.adk.events import Event
print('Event signature:', inspect.signature(Event))
print('Event public attrs/methods with response/final/content/text:')
for n,o in inspect.getmembers(Event):
    if n.startswith('_'):
        continue
    if any(k in n.lower() for k in ['final','content','text','function','partial']):
        if inspect.isfunction(o) or inspect.ismethoddescriptor(o):
            try:
                sig=str(inspect.signature(o))
            except Exception:
                sig='(?)'
            print(' ',n+sig)
        else:
            print(' ',n)

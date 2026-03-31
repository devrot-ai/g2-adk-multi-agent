import os

from google import genai

api_key = os.environ.get("GOOGLE_API_KEY")
if not api_key:
    print("GOOGLE_API_KEY is not set")
    print("WORKING_MODEL=NONE")
    raise SystemExit(0)

client = genai.Client(api_key=api_key)

raw_models = list(client.models.list())

candidates = []
seen = set()
for m in raw_models:
    name = getattr(m, "name", "") or ""
    model_id = name.split("/", 1)[-1] if name else ""

    actions = []
    for attr in ("supported_actions", "supported_generation_methods"):
        val = getattr(m, attr, None)
        if val:
            try:
                actions.extend(list(val))
            except Exception:
                pass

    supports_generate = any(str(a).lower() == "generatecontent" for a in actions)
    if "gemini" in model_id.lower() and supports_generate and model_id not in seen:
        seen.add(model_id)
        candidates.append(model_id)

candidates = sorted(candidates, key=lambda x: (("2.5" in x), x.lower()))
targets = candidates[:20]

print(f"CANDIDATE_COUNT={len(candidates)}")
print(f"TESTING_COUNT={len(targets)}")

working = None
for idx, model_name in enumerate(targets, 1):
    try:
        response = client.models.generate_content(model=model_name, contents="OK")
        text = (getattr(response, "text", "") or "").replace("\n", " ").strip()[:60] or "<no-text>"
        print(f"TRY {idx}: {model_name} -> OK ({text})")
        working = model_name
        break
    except Exception as e:
        msg = " ".join(str(e).replace("\n", " ").replace("\r", " ").split())[:180]
        print(f"TRY {idx}: {model_name} -> ERROR {msg}")

print(f"WORKING_MODEL={working if working else 'NONE'}")

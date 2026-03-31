import os

api_key = "AIzaSyAXDJb4dlkiltPy1HUspiBnye4U2V1nlIo"
os.environ["GOOGLE_API_KEY"] = api_key

candidate_models = [
    "gemini-2.0-flash",
    "gemini-2.0-flash-lite",
    "gemini-2.0-flash-001",
    "gemini-2.5-flash",
    "gemini-1.5-flash",
]

sdk = None
client = None
legacy_genai = None

try:
    from google import genai
    client = genai.Client(api_key=api_key)
    sdk = "google.genai"
except Exception as e_new:
    try:
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=api_key)
        sdk = "google.generativeai"
    except Exception as e_old:
        print(f"SDK_INIT: ERROR new={str(e_new).replace(chr(10),' ')[:120]} old={str(e_old).replace(chr(10),' ')[:120]}")
        print("BEST_NON_2_5=NONE")
        raise SystemExit(1)

results = {}

for model_name in candidate_models:
    try:
        if sdk == "google.genai":
            response = client.models.generate_content(
                model=model_name,
                contents="Reply with exactly: OK",
            )
            _ = getattr(response, "text", None)
        else:
            model = legacy_genai.GenerativeModel(model_name)
            response = model.generate_content("Reply with exactly: OK")
            _ = getattr(response, "text", None)

        results[model_name] = True
        print(f"{model_name}: OK")
    except Exception as ex:
        code = ""
        c = getattr(ex, "code", None)
        try:
            if callable(c):
                c_val = c()
            else:
                c_val = c
            if c_val is not None:
                code = str(c_val)
        except Exception:
            pass

        msg = str(ex).replace("\n", " ").replace("\r", " ")
        msg = " ".join(msg.split())
        excerpt = msg[:160]
        label = f"ERROR {code}".strip()
        print(f"{model_name}: {label} {excerpt}")
        results[model_name] = False

best = None
for m in ["gemini-2.0-flash", "gemini-2.0-flash-lite", "gemini-2.0-flash-001", "gemini-1.5-flash"]:
    if results.get(m):
        best = m
        break

print(f"BEST_NON_2_5={best if best else 'NONE'}")

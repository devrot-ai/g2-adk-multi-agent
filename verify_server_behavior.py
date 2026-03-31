import json
import requests

BASE = "http://localhost:8000"


def collect_model_texts(obj, out):
    if isinstance(obj, dict):
        content = obj.get("content")
        if isinstance(content, dict):
            role = str(content.get("role", "")).lower()
            if role in ("model", "assistant"):
                parts = content.get("parts", [])
                if isinstance(parts, list):
                    txt = " ".join(str(p.get("text", "")).strip() for p in parts if isinstance(p, dict) and p.get("text"))
                    if txt:
                        out.append(txt)
        role = str(obj.get("role", obj.get("author", ""))).lower()
        if role in ("model", "assistant"):
            parts = obj.get("parts", [])
            if isinstance(parts, list):
                txt = " ".join(str(p.get("text", "")).strip() for p in parts if isinstance(p, dict) and p.get("text"))
                if txt:
                    out.append(txt)
        for v in obj.values():
            collect_model_texts(v, out)
    elif isinstance(obj, list):
        for it in obj:
            collect_model_texts(it, out)


def collect_all_texts(obj, out):
    if isinstance(obj, dict):
        if isinstance(obj.get("text"), str) and obj.get("text").strip():
            out.append(obj["text"].strip())
        for v in obj.values():
            collect_all_texts(v, out)
    elif isinstance(obj, list):
        for it in obj:
            collect_all_texts(it, out)


def excerpt(text, n=180):
    t = " ".join(text.split())
    return t if len(t) <= n else t[:n-3] + "..."


results = {}

r1 = requests.get(f"{BASE}/list-apps", timeout=60)
results["list_apps_status"] = r1.status_code
results["list_apps_body"] = r1.text[:300]

r2 = requests.post(f"{BASE}/apps/summarizer_agent/users/u2/sessions/s2", json={}, timeout=60)
results["create_session_status"] = r2.status_code
results["create_session_body"] = r2.text[:300]

payload1 = {
    "appName": "summarizer_agent",
    "userId": "u2",
    "sessionId": "s2",
    "newMessage": {
        "role": "user",
        "parts": [
            {"text": "Classify this by topic and sentiment: ADK makes cloud deployment easier but setup can be difficult at first."}
        ]
    }
}
r3 = requests.post(f"{BASE}/run", json=payload1, timeout=120)
results["run_classification_status"] = r3.status_code
run1_excerpt = ""
if "application/json" in r3.headers.get("content-type", "").lower():
    data = r3.json()
    model_texts = []
    collect_model_texts(data, model_texts)
    if model_texts:
        run1_excerpt = excerpt(model_texts[-1])
    else:
        all_texts = []
        collect_all_texts(data, all_texts)
        run1_excerpt = excerpt(all_texts[-1]) if all_texts else ""
else:
    run1_excerpt = excerpt(r3.text)
results["run_classification_excerpt"] = run1_excerpt

payload2 = {
    "appName": "summarizer_agent",
    "userId": "u2",
    "sessionId": "s2",
    "newMessage": {
        "role": "user",
        "parts": [
            {"text": "Using this context: Cloud Run automatically scales stateless containers and charges by usage. Question: Why is Cloud Run cost efficient?"}
        ]
    }
}
r4 = requests.post(f"{BASE}/run", json=payload2, timeout=120)
results["run_grounded_qa_status"] = r4.status_code
run2_excerpt = ""
if "application/json" in r4.headers.get("content-type", "").lower():
    data = r4.json()
    model_texts = []
    collect_model_texts(data, model_texts)
    if model_texts:
        run2_excerpt = excerpt(model_texts[-1])
    else:
        all_texts = []
        collect_all_texts(data, all_texts)
        run2_excerpt = excerpt(all_texts[-1]) if all_texts else ""
else:
    run2_excerpt = excerpt(r4.text)
results["run_grounded_qa_excerpt"] = run2_excerpt

print(json.dumps(results, indent=2, ensure_ascii=False))

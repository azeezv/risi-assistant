import os
from typing import Any, cast
from google import genai
from dotenv import load_dotenv

load_dotenv()

if __name__ == "__main__":
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        print("GEMINI_API_KEY not set; set it to list available models.")
        raise SystemExit(0)

    client = genai.Client(api_key=api_key)

    # cast to Any to avoid strict stub/type issues in this environment
    pager = cast(Any, client.models).list()
    print("ListModels response:")

    # The returned object may be a google.genai.pagers.Pager which is iterable.
    # Iterate it and print a few useful fields for each model.
    count = 0
    for m in pager:
        count += 1
        # model may be a pydantic model object or a dict
        name = getattr(m, "name", None) or (m.get("name") if isinstance(m, dict) else None)
        # Common fields that may indicate capabilities
        supported = (
            getattr(m, "supported_methods", None)
            or getattr(m, "supported_generation_methods", None)
            or (m.get("supported_methods") if isinstance(m, dict) else None)
        )
        print(f"- {name}")
        if supported is not None:
            print("  supported:", supported)

    if count == 0:
        print("No models returned by ListModels.")
    else:
        print(f"Total models: {count}")

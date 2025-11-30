import sys
import os
import jinja2

# Ensure project root is on sys.path so `src` package can be imported when
# running this script directly.
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.lib.system_info import SystemInfo
from src.llm import GeminiProvider
from dotenv import load_dotenv

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.task", ""))
template = env.get_template("system.j2")

sys_prompt = template.render(
    user_os= SystemInfo.USER_OS,
    current_dir= SystemInfo.CURRENT_WORKING_DIRECTORY,
)

load_dotenv()

if __name__ == "__main__":
    try:
        # Require GEMINI_API_KEY to actually call the remote API. If missing,
        # print an informative message and exit so this script can be run
        # safely in CI/dev environments.
        if not os.environ.get("GEMINI_API_KEY"):
            print("GEMINI_API_KEY not set; set it to run a live Gemini test.")
            raise SystemExit(0)

        llm = GeminiProvider()

        queries = [
            "can you check whether docker installed on system or not ?"
            "List all available tools you can use to assist the user.",
            "What is the current operating system and its version?",
        ]

        try:
            resp = llm.inference(queries[0], system_prompt=sys_prompt)
            print("Gemini response:\n", resp)
        except Exception as e:
            print("Error running GeminiProvider.chat:", e)
    except KeyboardInterrupt:
        print("\n👋 Exiting")
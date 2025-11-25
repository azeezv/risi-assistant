import jinja2

env = jinja2.Environment(loader=jinja2.PackageLoader("src.agents.router", ""))
template = env.get_template("system.j2")

class RouterAgent:
    def __init__(self, tools: list[str]):
        self.tools = tools
        self.system_instruction = self.generate_system_instruction()

    def generate_system_instruction(self) -> str:
        return template.render(tools=self.tools)
    
    
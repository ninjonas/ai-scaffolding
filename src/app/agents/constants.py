from pathlib import Path

# Node and agent name constants used across agent graphs
NODE_LLM = "llm"
NODE_TOOLS = "tools"
NODE_ROUTER = "router"
NODE_END = "end"

AGENT_CHATBOT = "chatbot"
AGENT_RESEARCHER = "researcher"

# Shared directory paths
AGENTS_DIR = Path(__file__).parent
PROMPTS_DIR = AGENTS_DIR / "prompts"
RULES_DIR = AGENTS_DIR / "rules"

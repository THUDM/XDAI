# choose stable version for DEFAULT_CHATBOT
from .agent_base import AgentBase
from .xdai_glm import ChatAgentGLMBaseline
from .xdai_kg import ChatAgent_OPEN
from .xdai_kg_specific import ChatAgent_SP

IN_USE_AGENTS = [ChatAgentGLMBaseline, ChatAgent_OPEN]

IN_USE_AGENTS_DICT = {agent.version:agent for agent in IN_USE_AGENTS}

stable_version = None

class DEFAULT_CHATBOT(IN_USE_AGENTS[0]):
    activate_kw = None

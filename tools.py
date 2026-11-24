import ast
import math
import operator
import os
from contextvars import ContextVar

from dotenv import load_dotenv
import certifi

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from langchain_core.tools import tool

from rag import retrieve_from_rag
from database import save_memory, get_memories


# ---------------------------------------------------------------------------
# Current conversation (set by app.py before each agent run)
# ---------------------------------------------------------------------------

_current_thread_id: ContextVar[str] = ContextVar("current_thread_id", default="default")
_last_thread_id = "default"


def set_current_thread_id(thread_id: str) -> None:
    global _last_thread_id
    _current_thread_id.set(thread_id)
    _last_thread_id = thread_id


def get_current_thread_id() -> str:
    thread_id = _current_thread_id.get()

    # Tools may run in a worker thread that did not inherit the context.
    if thread_id == "default":
        return _last_thread_id

    return thread_id


# ---------------------------------------------------------------------------
# Tools
# ---------------------------------------------------------------------------

@tool
def search_uploaded_documents(query: str) -> str:
    """Search the documents the user uploaded in this conversation.
    Use this when the user asks about an uploaded file, PDF, or document."""

    return retrieve_from_rag(query, thread_id=get_current_thread_id())


@tool
def remember_this(fact: str) -> str:
    """Save an important fact or preference about the user so it can be recalled later.
    Use this when the user asks you to remember something."""

    save_memory(fact.strip())
    return f"Saved to memory: {fact.strip()}"


@tool
def recall_memory() -> str:
    """Recall facts and preferences previously saved about the user."""

    memories = get_memories()

    if not memories:
        return "No saved memories yet."

    return "\n".join(f"- {m.content}" for m in reversed(memories))


_OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.FloorDiv: operator.floordiv,
    ast.Mod: operator.mod,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos,
}

_FUNCTIONS = {
    name: getattr(math, name)
    for name in ("sqrt", "sin", "cos", "tan", "log", "log10", "exp", "floor", "ceil", "factorial")
}
_FUNCTIONS.update({"abs": abs, "round": round})

_CONSTANTS = {"pi": math.pi, "e": math.e}


def _safe_eval(node):
    if isinstance(node, ast.Expression):
        return _safe_eval(node.body)

    if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
        return node.value

    if isinstance(node, ast.Name) and node.id in _CONSTANTS:
        return _CONSTANTS[node.id]

    if isinstance(node, ast.BinOp) and type(node.op) in _OPERATORS:
        left, right = _safe_eval(node.left), _safe_eval(node.right)

        if isinstance(node.op, ast.Pow) and abs(right) > 1000:
            raise ValueError("Exponent too large.")

        return _OPERATORS[type(node.op)](left, right)

    if isinstance(node, ast.UnaryOp) and type(node.op) in _OPERATORS:
        return _OPERATORS[type(node.op)](_safe_eval(node.operand))

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id in _FUNCTIONS
        and not node.keywords
    ):
        return _FUNCTIONS[node.func.id](*[_safe_eval(arg) for arg in node.args])

    raise ValueError("Unsupported expression.")


@tool
def calculator(expression: str) -> str:
    """Evaluate a math expression, e.g. '2 * (3 + 4) ** 2' or 'sqrt(16) + log(10)'.
    Supports + - * / // % **, pi, e, and sqrt, sin, cos, tan, log, log10, exp, floor, ceil, factorial, abs, round."""

    try:
        result = _safe_eval(ast.parse(expression.replace("^", "**"), mode="eval"))
        return str(result)
    except Exception as e:
        return f"Could not calculate '{expression}': {e}"


tools = [
    search_uploaded_documents,
    remember_this,
    recall_memory,
    calculator,
]


# Web search is only available when a Tavily API key is configured.
if os.getenv("TAVILY_API_KEY"):
    from langchain_tavily import TavilySearch

    tools.append(
        TavilySearch(
            max_results=5,
            topic="general"
        )
    )
else:
    print("TAVILY_API_KEY not set - web search tool disabled.")

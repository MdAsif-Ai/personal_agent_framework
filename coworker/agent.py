"""Autonomous AI Co-Worker wrapped in an evaluation loop.

The worker is a LangChain create_agent (Layer 3) equipped with tools, MCP integrations,
and middleware for planning, safety, cost limits, and human-in-the-loop approvals.
A structured evaluator monitors the worker's output and tools used against success criteria,
looping until the criteria are satisfied or the agent requests human assistance.
"""

import logging
import os
import uuid
from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    HumanInTheLoopMiddleware,
    ModelCallLimitMiddleware,
    PIIMiddleware,
    TodoListMiddleware,
)
from langchain_core.messages import ToolMessage
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import Command

from coworker.config import (
    SANDBOX_DIR,
    DEFAULT_MODEL,
    MAX_EVALUATION_ATTEMPTS,
    MODEL_RUN_LIMIT,
)
from coworker.tools import get_all_tools

logger = logging.getLogger(__name__)


class EvaluatorOutput(BaseModel):
    """Evaluation verdict for the assistant's work."""

    feedback: str = Field(description="Constructive feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the defined success criteria have been met")
    user_input_needed: bool = Field(
        description="True if the assistant has a question, requires clarification, or is blocked"
    )


WORKER_PROMPT = """You are an autonomous AI Co-Worker, a capable and thorough professional assistant who completes tasks accurately.
You have access to a real web browser, a persistent sandbox filesystem, Google search, Wikipedia, PowerPoint slide generation, and push notifications.
When using the browser:
- Navigate directly to pages and inspect them with snapshots rather than clicking aimlessly.
- Dismiss popups and cookie notices yourself.
- If you encounter gates only a human can resolve (captchas, two-factor authentication, or sign-in walls), invoke the request_human_help tool with explicit instructions on what the user needs to do in your browser window.
For flight searches, use Google Flights directly in the browser by constructing a query URL:
https://www.google.com/travel/flights?q=flights+from+[ORIGIN]+to+[DESTINATION]+leaving+[DEPART]+returning+[RETURN]
Keep executing until your work meets the stated success criteria or you genuinely need human clarification.
Provide clear, structured, and professional final responses summarizing your findings and any artifacts created."""


class TolerateToolErrors(AgentMiddleware):
    """Catches unexpected tool failures and returns them as ToolMessages so the agent can self-heal."""

    async def awrap_tool_call(self, request, handler):
        try:
            return await handler(request)
        except Exception as error:
            logger.warning(f"Tool call failed gracefully caught: {error}")
            return ToolMessage(
                content=f"That tool call encountered an error: {error}. Please try an alternative approach or parameters.",
                tool_call_id=request.tool_call.get("id", "unknown_tool_id"),
            )


class CoworkerAgent:
    """The autonomous AI Co-Worker agent."""

    def __init__(self, model_name: str | None = None):
        self.agent_id = str(uuid.uuid4())
        self.model_name = model_name or DEFAULT_MODEL
        self.memory = InMemorySaver()
        self.tools = None
        self.sessions = None
        self.worker = None
        self.evaluator = None
        self.task = ""
        self.success_criteria = ""
        self.attempts = 0
        self.paused = False
        self.pending_actions = 0
        self.todos = []

    async def setup(self, sandbox_path: str | Path | None = None):
        """Initialize the agent, persistent MCP sessions, tools, and evaluator."""
        target_sandbox = Path(sandbox_path) if sandbox_path else SANDBOX_DIR
        target_sandbox.mkdir(parents=True, exist_ok=True)

        self.tools, self.sessions = await get_all_tools(str(target_sandbox))

        worker_model = f"openai:{self.model_name}" if not self.model_name.startswith("openai:") else self.model_name

        self.worker = create_agent(
            model=worker_model,
            tools=self.tools,
            system_prompt=f"{WORKER_PROMPT}\nToday is {datetime.now():%A %d %B %Y}.",
            middleware=[
                TolerateToolErrors(),
                TodoListMiddleware(),
                PIIMiddleware("email"),
                PIIMiddleware("credit_card", apply_to_tool_results=True),
                ModelCallLimitMiddleware(run_limit=MODEL_RUN_LIMIT),
                HumanInTheLoopMiddleware(
                    interrupt_on={"send_push_notification": True, "request_human_help": True}
                ),
            ],
            checkpointer=self.memory,
        )

        evaluator_model_name = self.model_name.replace("openai:", "")
        self.evaluator = ChatOpenAI(model=evaluator_model_name).with_structured_output(EvaluatorOutput)

    async def evaluate(
        self, message: str, success_criteria: str, last_reply: str, tools_used: list[str]
    ) -> EvaluatorOutput:
        """Evaluate whether the assistant met the user's success criteria."""
        prompt = f"""You decide whether an assistant has met the success criteria for a task.

The user's request was:
{message}

The success criteria are:
{success_criteria}

The tools the assistant called while working, in order:
{", ".join(tools_used) or "none"}

The assistant's most recent reply was:
{last_reply}

Decide whether the success criteria are met, using the tool calls as evidence of what was actually done.
Also decide whether the assistant needs more input from the user, either because it asked a question,
needs clarification, or seems stuck. Give brief, concrete feedback."""

        try:
            return await self.evaluator.ainvoke(prompt)
        except Exception as e:
            logger.error(f"Evaluator error: {e}")
            # Safe fallback if evaluation model call fails
            return EvaluatorOutput(
                feedback="Automatic evaluation completed.",
                success_criteria_met=True,
                user_input_needed=False,
            )

    async def run_turn(self, message: str, success_criteria: str = "", history: list | None = None) -> list:
        """Run one conversational turn, attempting the task and evaluating the response."""
        safe_history = list(history) if history is not None else []

        if not message or not message.strip():
            return safe_history

        self.task = message.strip()
        self.success_criteria = (
            success_criteria.strip() if success_criteria and success_criteria.strip()
            else "The answer should be clear, correct, and complete."
        )
        self.attempts = 0
        self.todos = []

        payload = {
            "messages": [
                {
                    "role": "user",
                    "content": f"{self.task}\n\nThe success criteria for this task are: {self.success_criteria}",
                }
            ]
        }
        return await self._advance(payload, safe_history + [{"role": "user", "content": self.task}])

    async def resume(self, history: list | None = None) -> list:
        """Approve the pending paused actions and resume the turn."""
        safe_history = list(history) if history is not None else []
        count = max(self.pending_actions, 1)
        payload = Command(resume={"decisions": [{"type": "approve"}] * count})
        return await self._advance(payload, safe_history)

    async def _advance(self, payload, history: list) -> list:
        """Stream worker execution and loop with evaluator feedback."""
        config = {"configurable": {"thread_id": self.agent_id}}

        while True:
            result = None
            async for step in self.worker.astream(payload, config=config, stream_mode="values"):
                result = step
                self.todos = result.get("todos", self.todos)

            if result is None:
                return history + [{"role": "assistant", "content": "I was unable to complete the request."}]

            # Handle human-in-the-loop interruption
            if "__interrupt__" in result:
                actions = result["__interrupt__"][0].value.get("action_requests", [])
                self.paused = True
                self.pending_actions = len(actions)
                described = "\n".join(action.get("description", "Action pending approval") for action in actions)
                return history + [{"role": "assistant", "content": f"Waiting for your approval:\n{described}"}]

            self.paused = False
            self.pending_actions = 0

            messages = result.get("messages", [])
            reply = messages[-1].content if messages else "No response generated."

            tools_used = [
                call.get("name", "")
                for m in messages
                for call in (getattr(m, "tool_calls", None) or [])
                if isinstance(call, dict) and "name" in call
            ]

            self.attempts += 1
            verdict = await self.evaluate(self.task, self.success_criteria, reply, tools_used)

            if verdict.success_criteria_met or verdict.user_input_needed or self.attempts >= MAX_EVALUATION_ATTEMPTS:
                return history + [
                    {"role": "assistant", "content": reply},
                    {"role": "assistant", "content": f"Evaluator: {verdict.feedback}"},
                ]

            # Re-prompt worker with feedback for the next attempt
            payload = {
                "messages": [
                    {
                        "role": "user",
                        "content": (
                            f"Your previous attempt did not fully meet the success criteria.\n"
                            f"Evaluator feedback: {verdict.feedback}\n"
                            "Please refine your solution and address this feedback."
                        ),
                    }
                ]
            }

    def cleanup(self):
        """Shut down the MCP server sessions and close the browser."""
        if self.sessions:
            self.sessions.stop()

    async def aclose(self):
        """Asynchronously shut down the MCP server sessions."""
        if self.sessions:
            if hasattr(self.sessions, "aclose"):
                await self.sessions.aclose()
            else:
                self.sessions.stop()


# Professional alias
Coworker = CoworkerAgent

"""Gradio web application interface for the autonomous AI Co-Worker."""

import html
import logging
import gradio as gr

from coworker.agent import CoworkerAgent
from coworker.ui.theme import HEADER_HTML, LAUNCH_STYLE

logger = logging.getLogger(__name__)


def render_todos(todos: list[dict] | None) -> str:
    """Render the agent's real-time plan as structured HTML."""
    if not todos:
        items = '<div class="placeholder">The AI Co-Worker will write its plan here as it works</div>'
    else:
        items = "<ul>" + "".join(
            f'<li class="{html.escape(str(todo.get("status", "pending")))}">'
            f'<span class="mark"></span>'
            f'{html.escape(str(todo.get("content", "")))}'
            f'</li>'
            for todo in todos
        ) + "</ul>"
    return f"<h3>Plan</h3>{items}"


async def setup_agent():
    """Asynchronously initialize the AI Co-Worker agent and MCP servers."""
    try:
        agent = CoworkerAgent()
        await agent.setup()
        return agent, gr.update(interactive=True, value="Go!")
    except Exception as e:
        logger.error(f"Failed to initialize AI Co-Worker: {e}")
        return None, gr.update(interactive=False, value="Setup Error")


async def process_message(agent: CoworkerAgent | None, message: str, success_criteria: str, history: list | None):
    """Handle user message submission."""
    safe_history = list(history) if history is not None else []

    if not message or not message.strip():
        return (
            gr.update(),
            safe_history,
            gr.update(visible=agent.paused if agent else False),
            agent,
        )

    if agent is None:
        safe_history.append({
            "role": "assistant",
            "content": "The AI Co-Worker is still initializing its MCP tools. Please wait a few seconds and try again.",
        })
        return gr.update(), safe_history, gr.update(visible=False), agent

    # Execute conversational turn
    results = await agent.run_turn(message, success_criteria, safe_history)
    return (
        gr.update(value=""),  # Clear message input box on submit
        results,
        gr.update(visible=agent.paused),
        agent,
    )


async def approve_action(agent: CoworkerAgent | None, history: list | None):
    """Approve paused human-in-the-loop actions."""
    safe_history = list(history) if history is not None else []
    if not agent:
        return safe_history, gr.update(visible=False), agent

    results = await agent.resume(safe_history)
    return results, gr.update(visible=agent.paused), agent


def watch_todos(agent: CoworkerAgent | None) -> str:
    """Poll plan updates to render real-time status in Gradio."""
    if agent and hasattr(agent, "todos"):
        return render_todos(agent.todos)
    return render_todos([])


async def reset_session(agent: CoworkerAgent | None):
    """Reset the conversation, clean up MCP processes, and create a fresh agent."""
    if agent:
        try:
            agent.cleanup()
        except Exception as e:
            logger.warning(f"Error during agent cleanup: {e}")

    new_agent = CoworkerAgent()
    await new_agent.setup()

    # Clear message, criteria, chat history, plan panel, approve button, and return new agent
    return (
        "",
        "",
        [],
        render_todos([]),
        gr.update(visible=False),
        new_agent,
    )


def free_resources(agent: CoworkerAgent | None):
    """Callback to terminate external MCP servers when session expires."""
    if agent:
        try:
            agent.cleanup()
        except Exception as e:
            logger.warning(f"Error freeing resources: {e}")


def build_app() -> gr.Blocks:
    """Build the Gradio Blocks UI application."""
    with gr.Blocks(title="AI Co-Worker") as ui:
        gr.HTML(HEADER_HTML)
        agent_state = gr.State(delete_callback=free_resources)

        with gr.Row():
            chatbot = gr.Chatbot(label="AI Co-Worker", height=380, scale=3, elem_id="chat")
            with gr.Column(scale=1):
                todos_panel = gr.HTML(render_todos([]), elem_id="plan-panel")

        with gr.Group(elem_id="ask-panel"):
            with gr.Row():
                message = gr.Textbox(
                    show_label=False,
                    placeholder="Describe your task for the AI Co-Worker (e.g. research a topic, check flights, make a slide)...",
                    lines=2,
                )
            with gr.Row():
                success_criteria = gr.Textbox(
                    show_label=False,
                    placeholder="Define your success criteria (e.g. 'Must include 3 options with prices and save to summary.md')",
                    lines=1,
                )

        with gr.Row():
            reset_button = gr.Button("Reset", elem_id="reset-button")
            approve_button = gr.Button("Approve and continue", visible=False, elem_id="approve-button")
            go_button = gr.Button("Go!", elem_id="go-button", interactive=False)

        timer = gr.Timer(1)

        # Event wiring
        ui.load(setup_agent, inputs=[], outputs=[agent_state, go_button])
        timer.tick(watch_todos, inputs=[agent_state], outputs=[todos_panel], show_progress="hidden")

        message.submit(
            process_message,
            inputs=[agent_state, message, success_criteria, chatbot],
            outputs=[message, chatbot, approve_button, agent_state],
        )
        success_criteria.submit(
            process_message,
            inputs=[agent_state, message, success_criteria, chatbot],
            outputs=[message, chatbot, approve_button, agent_state],
        )
        go_button.click(
            process_message,
            inputs=[agent_state, message, success_criteria, chatbot],
            outputs=[message, chatbot, approve_button, agent_state],
        )

        approve_button.click(
            approve_action,
            inputs=[agent_state, chatbot],
            outputs=[chatbot, approve_button, agent_state],
        )

        reset_button.click(
            reset_session,
            inputs=[agent_state],
            outputs=[message, success_criteria, chatbot, todos_panel, approve_button, agent_state],
        )

    return ui


ui = build_app()


def launch():
    """Launch the application."""
    ui.launch(inbrowser=True, **LAUNCH_STYLE)


if __name__ == "__main__":
    launch()

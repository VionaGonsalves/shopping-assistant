import sys

from anthropic import AsyncAnthropic, APIError
from fastapi import APIRouter, Depends, HTTPException, status
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

from ..auth import get_current_user, oauth2_scheme
from ..configs import settings
from ..models import Users
from ..schemas import ChatRequest, ChatResponse

conversations: dict[int, list[dict]] = {}
MAX_HISTORY = 20

router = APIRouter(prefix="/chat", tags=["chat"])
claude = AsyncAnthropic(api_key=settings.anthropic_api_key)

MAX_TOOL_ROUNDS = 5

SYSTEM_PROMPT = """You are a helpful shopping assistant for a car store. Prices are in INR.
- Use the tools for any product, price or cart information. Never state a price that did not come from a tool result.
- If you only know a car's name, use search_products to find its id first.
- Before calling add_to_cart, confirm the exact car and quantity with the user and wait for a clear yes.
- If a tool returns an error, briefly tell the user what went wrong. Do not guess.
- Keep answers short and friendly.
- Only say an action happened (e.g. added to cart) if a tool result in this conversation confirms it."""

def trim_history(history: list[dict]) -> None:
    """Keep recent messages, but never cut between a tool call and its result."""
    if len(history) <= MAX_HISTORY:
        return
    cut = len(history) - MAX_HISTORY
    # move the cut forward to the start of a real user turn (plain text, not tool results)
    while cut < len(history) and not (
        history[cut]["role"] == "user" and isinstance(history[cut]["content"], str)
    ):
        cut += 1
    del history[:cut]

@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    current_user: Users = Depends(get_current_user),   # must be logged in
    token: str = Depends(oauth2_scheme),                # the raw JWT, passed to MCP
):
    # Start the MCP server as this user
    server = StdioServerParameters(
        command=sys.executable,
        args=["mcp_server/server.py"],
        env={"SHOP_API_TOKEN": token},
    )

    history = conversations.setdefault(current_user.id, [])
    user_message = {"role": "user", "content": request.message}
    messages = history + [user_message]

    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Convert MCP's tool list into Claude's tool format
            mcp_tools = await session.list_tools()
            tools = [
                {"name": t.name, "description": t.description, "input_schema": t.inputSchema}
                for t in mcp_tools.tools
            ]

            for _ in range(MAX_TOOL_ROUNDS):
                try:
                    response = await claude.messages.create(
                        model=settings.anthropic_model,
                        max_tokens=1024,
                        system=SYSTEM_PROMPT,
                        messages=messages,
                        tools=tools,
                    )
                except APIError:
                    raise HTTPException(status_code=status.HTTP_502_BAD_GATEWAY,
                                        detail="The AI service is unavailable, please try again.")

                # Claude answered with text: we're done
                if response.stop_reason != "tool_use":
                    reply = "".join(b.text for b in response.content if b.type == "text")
                    messages.append({"role": "assistant", "content": response.content})
                    history[:] = messages            # full exchange: user msg, tool calls, results, reply
                    trim_history(history)
                    return ChatResponse(reply=reply)
                
                # Claude asked for tools: record its request, run each tool, send results back
                messages.append({"role": "assistant", "content": response.content})

                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        result = await session.call_tool(block.name, block.input)
                        text = "".join(c.text for c in result.content if c.type == "text")
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": text,
                            "is_error": bool(result.isError),
                        })

                messages.append({"role": "user", "content": tool_results})

    return ChatResponse(reply="Sorry, I couldn't complete that request. Please try rephrasing.")

@router.delete("", status_code=status.HTTP_204_NO_CONTENT)
async def clear_chat(current_user: Users = Depends(get_current_user)):
    conversations.pop(current_user.id, None)
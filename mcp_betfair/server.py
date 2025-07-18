import datetime as dt
from typing import Optional, List
import os
import dotenv
from pydantic_ai import (Agent, RunContext)
from starlette.responses import RedirectResponse
from mem0 import AsyncMemoryClient
from mcp_betfair.betfair_client import BetfairClient
from mcp_betfair.database import Database
import json
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated, Literal

import fastapi
import logfire
from fastapi import Depends, Request
from fastapi.responses import FileResponse, Response, StreamingResponse
from typing_extensions import TypedDict
from pydantic_ai.exceptions import UnexpectedModelBehavior
from pydantic_ai.messages import (
    ModelMessage,
    ModelRequest,
    ModelResponse,
    TextPart,
    UserPromptPart,
)

dotenv.load_dotenv()

# Initialize Betfair client with environment variables
betfair_client = BetfairClient(
    api_key=os.getenv('BETFAIR_API_KEY'),
    session_token=os.getenv('BETFAIR_SESSION_TOKEN'),
)


THIS_DIR = os.path.dirname(os.path.abspath(__file__))


@asynccontextmanager
async def lifespan(_app: fastapi.FastAPI):
    client = AsyncMemoryClient(host="http://localhost:8888", api_key="not-needed")
    async with Database.connect() as db:
        yield {'db': db, 'memory': client}


agent = Agent(
    'google-gla:gemini-2.0-flash',
    system_prompt=(
        "You're an aggressive bookmaker, you're keen to take bets on any sporting event. "
        "You have access to the Betfair API, which allows you to retrieve market data. "
        "You can use this data to answer questions about sports events, odds, and betting markets. "
        "The general flow is to first list the sports types, then list the events, "
        "then list the competitions, list market catalogue, and then return market selection."
        "If the user asks for odds, you should return the current odds for the market selection."
    ),
)

app = fastapi.FastAPI(lifespan=lifespan)
logfire.instrument_fastapi(app)


@agent.tool
def list_sport_types(ctx: RunContext[str]):
    """
    List sport types from Betfair API, this will return a list like
    [{'id': '1', 'EventType': 'Soccer'}, {'id': '2', 'EventType': 'Tennis'}, ...]
    The ids can be used in further queries to filter events/markets/competitions by event_type_id.
    """
    return betfair_client.list_event_types()


@agent.tool
def list_events(
    ctx: RunContext[str],
    event_type_ids: Optional[List[int]] = None,
    market_start_time: Optional[dt.datetime] = None,
    market_end_time: Optional[dt.datetime] = None,
):
    """
    ** Event Type ids can be found from the `list_sport_types` tool.
    List the events available on Betfair based on various filters.
    :param event_type_ids: List of event type IDs to filter events. # Optional
    :param market_start_time: The start time to search what events are available to bet on. # Optional
    :param market_end_time: The end time to search what events are available to bet on. # Optional
    """
    return betfair_client.list_events(
        event_type_ids=event_type_ids,
        market_start_time=market_start_time,
        market_end_time=market_end_time,
    )


@agent.tool
def list_competitions(
    ctx: RunContext[str],
    text_query: Optional[str] = None,
    exchange_ids: Optional[List[int]] = None,
    event_ids: Optional[List[int]] = None,
    event_type_ids: Optional[List[int]] = None,
):
    """
    List competitions based on various filters.
    ** Event Type ids can be found from the `list_sport_types` tool.

    Sometimes you may want to get markets based on the competition.
    An example may be the Brownlow medal, or the EPL. Let's have a look at all the soccer
    competitions over the next week and filter to only get the EPL Competition ID.

    :param text_query: Text query to filter competitions. # Optional
    :param exchange_ids: List of exchange IDs to filter competitions. # Optional
    :param event_ids: List of event IDs to filter competitions. # Optional
    :param event_type_ids: List of event type IDs to filter competitions. # Optional
    """
    return betfair_client.list_competitions(
        text_query=text_query,
        exchange_ids=exchange_ids,
        event_ids=event_ids,
        event_type_ids=event_type_ids,
    )


@agent.tool
def list_market_types(
    ctx: RunContext[str],
    event_type_ids: Optional[List[int]] = None,
):
    """
    List market types based on event type IDs.

    If we want to know the various market types that there are for a particular event,
    as well as how much has been matched on each market, we want to request data from the
    listMarketTypes operation. We can provide a number of filters, including the
    Event Type ID to the filter.

    :param ctx:
    :param event_type_ids: List of event type IDs to filter market types. If not provided, all event types will be considered.
    :return:
    """
    return betfair_client.list_market_types(event_type_ids=event_type_ids)


@agent.tool
def list_market_catalogue(
    ctx: RunContext[str],
    event_type_ids: Optional[List[str]] = None,
    event_ids: Optional[List[int]] = None,
    competition_ids: Optional[List[int]] = None,
    market_start_time: Optional[dt.datetime] = None,
    market_end_time: Optional[dt.datetime] = None,
):
    """
    List market catalogue based on various filters.

    If we want to know the various market names that there are for a particular event,
    as well as how much has been matched on each market, we want to request data from the
    listMarketCatalogue operation. We can provide a number of filters, including the
    Competition ID, the Event ID, the Venue etc. to the filter.

    :param ctx:
    :param event_ids: List of event IDs to filter markets. If not provided, all events will be considered.
    :param competition_ids: List of competition IDs to filter markets. If not provided, all competitions will be considered.
    :param market_type_codes: List of market type codes to filter markets. If not provided, all market types will be considered.
    :param market_start_time: The start time to search for markets. If not provided, all markets will be considered.
    :param market_end_time: The end time to search for markets. If not provided, all markets will be considered.
    :return:
    """
    return betfair_client.list_market_catalogue(
        event_type_ids=event_type_ids,
        event_ids=event_ids,
        competition_ids=competition_ids,
        market_start_time=market_start_time,
        market_end_time=market_end_time,
    )

@agent.tool
def list_market_book_selections(
    ctx: RunContext[str],
    market_ids: Optional[List[str]] = None,
):
    """
    List market book selections based on various filters.

    If we want to know the current odds for a particular market, we want to request data from the
    listMarketBook operation. We can provide a number of filters, including the Market ID, the Selection ID etc.
    to the filter.

    :param ctx:
    :param market_ids: List of market IDs to filter selections. If not provided, all markets will be considered.
    :param selection_ids: List of selection IDs to filter selections. If not provided, all selections will be considered.
    :return:
    """
    return betfair_client.list_market_book_selections(
        market_ids=market_ids,
    )

@agent.tool
def search_memories(
    ctx: RunContext[str],
    user_id: str,
    query: str,
):
    """
    Search a users previous chats with the agent.
    The memories are all the previous interactions the user has had with the agent.
    This might be useful to add a bit of context to the conversation, or to
    avoid repeating the same question multiple times.

    This tool allows you to search for memories stored in the memory store.
    It returns a list of memories that match the query.

    :param user_id: The ID of the user whose memories are being searched.
    :param session_id: The ID of the session for which memories are being searched.
    :param query: The query string to search for in the memories.
    :return: A list of memories that match the query.
    """
    memory_client = AsyncMemoryClient(host="http://localhost:8888", api_key="not-needed")
    return memory_client.search(user_id=user_id, query=query)


@app.get('/start/')
async def start_page() -> FileResponse:
    return FileResponse((os.path.join(THIS_DIR, '../public/start.html')), media_type='text/html')


@app.get('/')
async def index() -> RedirectResponse:
    return RedirectResponse(url='/start/')


@app.get('/chat')
async def index() -> FileResponse:
    return FileResponse((os.path.join(THIS_DIR, '../public/chat_app.html')), media_type='text/html')


@app.get('/chat_app.ts')
async def main_ts() -> FileResponse:
    """Get the raw typescript code, it's compiled in the browser, forgive me."""
    return FileResponse((os.path.join(THIS_DIR, '../public/chat_app.ts')), media_type='text/plain')


async def get_db(request: Request) -> Database:
    return request.state.db


async def get_memory_store(request: Request) -> AsyncMemoryClient:
    return request.state.memory


@app.get('/chat-messages/')
async def get_chat(
    username: str,
    session_id: str,
    database: Database = Depends(get_db),
    memory_store: AsyncMemoryClient = Depends(get_memory_store),
) -> Response:
    msgs = await database.get_messages(username, session_id)
    memories = await memory_store.get_all(user_id=username, run_id=session_id)
    return Response(
        b'\n'.join(json.dumps(to_chat_message(m)).encode('utf-8') for m in msgs),
        media_type='text/plain',
    )


class ChatMessage(TypedDict):
    """Format of messages sent to the browser."""

    role: Literal['user', 'model']
    timestamp: str
    content: str


def to_chat_message(m: ModelMessage) -> ChatMessage:
    first_part = m.parts[0]
    if isinstance(m, ModelRequest):
        if isinstance(first_part, UserPromptPart):
            assert isinstance(first_part.content, str)
            return {
                'role': 'user',
                'timestamp': first_part.timestamp.isoformat(),
                'content': first_part.content,
            }
    elif isinstance(m, ModelResponse):
        if isinstance(first_part, TextPart):
            return {
                'role': 'model',
                'timestamp': m.timestamp.isoformat(),
                'content': first_part.content,
            }
    raise UnexpectedModelBehavior(f'Unexpected message type for chat app: {m}')


def convert_pydantic_to_chat_message(
    pydantic_msg: ModelMessage,
) -> List[ChatMessage]:
    """Convert a Pydantic message to a chat message format."""
    format_memories = []
    if isinstance(pydantic_msg, ModelRequest):
        for part in pydantic_msg.parts:
            if isinstance(part, UserPromptPart):
                format_memories.append({
                    'role': 'user',
                    'content': part.content,
                })
    elif isinstance(pydantic_msg, ModelResponse):
        for part in pydantic_msg.parts:
            if isinstance(part, TextPart):
                format_memories.append({
                    'role': 'model',
                    'content': part.content,
                })
    return []


@app.post('/chat-messages/')
async def post_chat(
    username: Annotated[str, fastapi.Form()],
    session_id: Annotated[str, fastapi.Form()],
    prompt: Annotated[str, fastapi.Form()],
    database: Database = Depends(get_db),
    memory_store: AsyncMemoryClient = Depends(get_memory_store),
) -> StreamingResponse:
    async def stream_messages():
        yield (
            json.dumps(
                {
                    'role': 'user',
                    'timestamp': datetime.now(tz=timezone.utc).isoformat(),
                    'content': prompt,
                }
            ).encode('utf-8')
            + b'\n'
        )
        messages = await database.get_messages(username, session_id)
        async with agent.run_stream(prompt, message_history=messages) as result:
            async for text in result.stream(debounce_by=0.01):
                m = ModelResponse(parts=[TextPart(text)], timestamp=result.timestamp())
                yield json.dumps(to_chat_message(m)).encode('utf-8') + b'\n'

        await database.add_messages(username, session_id, result.new_messages_json())
        format_memories = []
        for m in result.new_messages():
            converted = convert_pydantic_to_chat_message(m)
            if converted:
                format_memories.extend(converted)
        if format_memories:
            await memory_store.add(
                messages=format_memories,
                user_id=username,
                run_id=session_id,
            )

    return StreamingResponse(stream_messages(), media_type='text/plain')

from __future__ import annotations
import json
import re
import logging
from typing import AsyncGenerator
from openai import AsyncOpenAI, APITimeoutError, APIConnectionError, APIStatusError
from app.core.config import get_settings
from app.agent.tools import get_tools_definition
from app.agent.tool_executor import ToolExecutor
from app.agent.context_builder import ContextBuilder
from app.services.session_service import SessionService
from app.services.route_service import RouteService
from app.models.session import ChatMessage

logger = logging.getLogger(__name__)


class AgentEngine:
    MAX_ITERATIONS = 20

    def __init__(self):
        self.settings = get_settings()
        self.client = AsyncOpenAI(
            api_key=self.settings.OPENAI_API_KEY,
            base_url=self.settings.OPENAI_BASE_URL,
            timeout=60.0,
        )
        self.tool_executor = ToolExecutor()
        self.context_builder = ContextBuilder()
        self.session_service = SessionService()
        self.route_service = RouteService()

    async def chat(
        self,
        session_id: str,
        user_id: str,
        question: str,
    ) -> AsyncGenerator[dict, None]:
        try:
            await self.session_service.get_or_create_session(session_id, user_id)
            await self.session_service.add_message(
                session_id, ChatMessage(role="user", content=question)
            )
        except Exception as e:
            logger.warning(f"Session init failed: {e}")

        try:
            messages = await self.context_builder.build_messages(
                session_id, user_id, question
            )
        except Exception as e:
            logger.warning(f"Context build failed, using minimal context: {e}")
            from app.agent.prompts import build_system_prompt
            messages = [
                {"role": "system", "content": build_system_prompt()},
                {"role": "user", "content": question},
            ]

        tools = get_tools_definition()
        new_messages = []

        try:
            async for event in self._agent_loop(messages, tools, user_id):
                yield event
                if event.get("type") == "text" and event.get("content"):
                    pass
                if event.get("type") == "route_recommendations":
                    pass
        except APITimeoutError:
            yield {
                "type": "error",
                "content": "AI 服务响应超时，请稍后重试。可能是因为网络连接不稳定或 API 服务繁忙。",
            }
        except APIConnectionError:
            yield {
                "type": "error",
                "content": "无法连接到 AI 服务，请检查网络连接和 API 配置。如果你使用的是自定义 API 地址，请确认 OPENAI_BASE_URL 配置正确。",
            }
        except APIStatusError as e:
            if e.status_code == 401:
                yield {
                    "type": "error",
                    "content": "API 密钥无效，请检查 OPENAI_API_KEY 配置。",
                }
            elif e.status_code == 429:
                yield {
                    "type": "error",
                    "content": "API 调用频率超限，请稍后重试。",
                }
            else:
                yield {
                    "type": "error",
                    "content": f"AI 服务返回错误 (HTTP {e.status_code})，请稍后重试。",
                }
        except Exception as e:
            logger.error(f"Agent loop unexpected error: {e}", exc_info=True)
            yield {
                "type": "error",
                "content": f"智能助手暂时无法响应，请稍后重试。",
            }

        if new_messages:
            try:
                await self.session_service.add_messages(session_id, new_messages)
            except Exception as e:
                logger.warning(f"Session save failed: {e}")

    async def _agent_loop(
        self, messages: list, tools: list, user_id: str
    ) -> AsyncGenerator[dict, None]:
        new_messages = []

        for iteration in range(self.MAX_ITERATIONS):
            response = await self.client.chat.completions.create(
                model=self.settings.OPENAI_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                stream=True,
            )

            collected_content = ""
            collected_tool_calls = {}
            tool_call_started = False

            async for chunk in response:
                delta = chunk.choices[0].delta if chunk.choices else None
                if not delta:
                    continue

                if delta.content:
                    collected_content += delta.content
                    yield {
                        "type": "text",
                        "content": delta.content,
                    }

                if delta.tool_calls:
                    tool_call_started = True
                    for tc in delta.tool_calls:
                        idx = tc.index
                        if idx not in collected_tool_calls:
                            collected_tool_calls[idx] = {
                                "id": "",
                                "function": {"name": "", "arguments": ""},
                                "type": "function",
                            }
                        if tc.id:
                            collected_tool_calls[idx]["id"] = tc.id
                        if tc.function:
                            if tc.function.name:
                                collected_tool_calls[idx]["function"]["name"] += tc.function.name
                            if tc.function.arguments:
                                collected_tool_calls[idx]["function"]["arguments"] += tc.function.arguments

            if not tool_call_started and collected_content:
                assistant_msg = {"role": "assistant", "content": collected_content}
                messages.append(assistant_msg)
                new_messages.append(ChatMessage(role="assistant", content=collected_content))

                route_names = self._extract_route_names(collected_content)
                if route_names:
                    try:
                        routes = await self.route_service.fuzzy_match_routes(route_names)
                        if routes:
                            yield {
                                "type": "route_recommendations",
                                "routes": routes,
                            }
                    except Exception as e:
                        logger.warning(f"Route fuzzy match failed: {e}")

                break

            if collected_tool_calls:
                tool_calls_list = list(collected_tool_calls.values())
                assistant_msg = {
                    "role": "assistant",
                    "content": collected_content or None,
                    "tool_calls": tool_calls_list,
                }
                messages.append(assistant_msg)
                new_messages.append(
                    ChatMessage(
                        role="assistant",
                        content=collected_content or "",
                        tool_calls=tool_calls_list,
                    )
                )

                for tc in tool_calls_list:
                    tool_name = tc["function"]["name"]
                    try:
                        tool_args = json.loads(tc["function"]["arguments"])
                    except json.JSONDecodeError:
                        tool_args = {}

                    yield {
                        "type": "tool_call",
                        "tool_name": tool_name,
                        "arguments": tool_args,
                    }

                    try:
                        tool_result = await self.tool_executor.execute(
                            tool_name, tool_args, user_id
                        )
                    except Exception as e:
                        tool_result = json.dumps({"error": str(e)}, ensure_ascii=False)

                    yield {
                        "type": "tool_result",
                        "tool_name": tool_name,
                        "result": json.loads(tool_result) if isinstance(tool_result, str) else tool_result,
                    }

                    tool_msg = {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_result,
                    }
                    messages.append(tool_msg)
                    new_messages.append(
                        ChatMessage(
                            role="tool",
                            content=tool_result,
                            tool_call_id=tc["id"],
                        )
                    )
            else:
                break

    def _extract_route_names(self, text: str) -> list[str]:
        names = []
        patterns = [
            r'《([^》]+)》',
            r'「([^」]+)」',
            r'\*\*([^*]+)\*\*',
            r'路线[：:]\s*([^\n,，、]+)',
        ]
        for pattern in patterns:
            matches = re.findall(pattern, text)
            names.extend(matches)

        seen = set()
        unique = []
        for n in names:
            n = n.strip()
            if n and n not in seen and len(n) > 1 and len(n) < 50:
                seen.add(n)
                unique.append(n)
        return unique[:5]

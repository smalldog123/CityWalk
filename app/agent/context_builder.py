from __future__ import annotations
from app.services.session_service import SessionService
from app.services.user_service import UserService
from app.agent.prompts import build_system_prompt


class ContextBuilder:
    def __init__(self):
        self.session_service = SessionService()
        self.user_service = UserService()

    async def build_messages(
        self,
        session_id: str,
        user_id: str,
        current_question: str,
    ) -> list[dict]:
        system_prompt = build_system_prompt()
        preference_context = await self._build_preference_context(user_id)
        if preference_context:
            system_prompt += f"\n\n## 当前用户偏好\n{preference_context}"

        history = await self.session_service.get_messages(session_id)
        messages = [{"role": "system", "content": system_prompt}]

        for msg in history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if role in ("user", "assistant"):
                messages.append({"role": role, "content": content})
            elif role == "tool":
                messages.append({
                    "role": "tool",
                    "content": content,
                    "tool_call_id": msg.get("tool_call_id", ""),
                })
            elif role == "assistant" and msg.get("tool_calls"):
                messages.append({
                    "role": "assistant",
                    "content": content or None,
                    "tool_calls": msg["tool_calls"],
                })

        messages.append({"role": "user", "content": current_question})
        return messages

    async def _build_preference_context(self, user_id: str) -> str:
        if not user_id:
            return ""
        preference = await self.user_service.get_user_preference(user_id)
        if not preference:
            return ""

        parts = []
        if preference.get("cities"):
            parts.append(f"常去城市：{', '.join(preference['cities'])}")
        if preference.get("difficulties"):
            parts.append(f"偏好难度：{', '.join(preference['difficulties'])}")
        if preference.get("tags"):
            parts.append(f"偏好标签：{', '.join(preference['tags'])}")
        if preference.get("avg_distance"):
            parts.append(f"平均距离：{preference['avg_distance']}km")

        return "；".join(parts) if parts else ""

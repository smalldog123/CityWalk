TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_routes",
            "description": "搜索徒步路线。可根据城市、难度、距离范围、标签等条件筛选路线，也可通过关键词模糊搜索路线名称和描述。",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "城市名称，如'北京'、'杭州'、'成都'",
                    },
                    "difficulty": {
                        "type": "string",
                        "enum": ["easy", "moderate", "hard", "expert"],
                        "description": "路线难度等级：easy=简单, moderate=中等, hard=困难, expert=专家",
                    },
                    "min_distance": {
                        "type": "number",
                        "description": "最短距离（公里）",
                    },
                    "max_distance": {
                        "type": "number",
                        "description": "最长距离（公里）",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "路线标签，如['山景', '湖景', '森林']",
                    },
                    "keyword": {
                        "type": "string",
                        "description": "关键词，用于模糊搜索路线名称和描述",
                    },
                    "limit": {
                        "type": "integer",
                        "description": "返回结果数量，默认10",
                        "default": 10,
                    },
                },
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_knowledge",
            "description": "从知识图谱中检索路线、POI、标签、城市之间的关联信息。支持语义搜索，可根据自然语言描述查找相关路线、景点、标签等。当用户询问路线特色、沿途景点、相似路线推荐等需要关联信息的问题时使用。",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "搜索查询文本，可以是路线名、景点名、标签、城市名或自然语言描述",
                    },
                    "search_type": {
                        "type": "string",
                        "enum": ["semantic", "city", "tag", "poi", "entity"],
                        "description": "搜索类型：semantic=语义搜索, city=按城市搜索路线, tag=按标签搜索路线, poi=搜索路线沿途景点, entity=按实体名搜索",
                        "default": "semantic",
                    },
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_preference",
            "description": "获取用户的历史偏好信息，包括常去城市、偏好难度、偏好标签、平均距离等。用于个性化推荐路线。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户ID",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "update_user_preference",
            "description": "更新用户的偏好信息。可手动设置或由系统自动学习更新。支持更新偏好城市、难度、标签等。",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {
                        "type": "string",
                        "description": "用户ID",
                    },
                    "cities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "偏好城市列表",
                    },
                    "difficulties": {
                        "type": "array",
                        "items": {
                            "type": "string",
                            "enum": ["easy", "moderate", "hard", "expert"],
                        },
                        "description": "偏好难度列表",
                    },
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "偏好标签列表",
                    },
                },
                "required": ["user_id"],
            },
        },
    },
]


def get_tools_definition() -> list[dict]:
    return TOOLS

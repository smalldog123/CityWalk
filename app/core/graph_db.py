from falkordb import FalkorDB
from app.core.config import get_settings
from typing import Optional

_graph: Optional[object] = None


def get_falkordb_graph():
    global _graph
    if _graph is None:
        settings = get_settings()
        db = FalkorDB(host=settings.FALKORDB_HOST, port=settings.FALKORDB_PORT)
        _graph = db.select_graph("citywalk_kg")
    return _graph


async def init_knowledge_graph():
    graph = get_falkordb_graph()
    graph.query("""
        MERGE (c:City {name: '北京'})
        MERGE (c2:City {name: '上海'})
        MERGE (c3:City {name: '杭州'})
        MERGE (c4:City {name: '成都'})
        MERGE (c5:City {name: '深圳'})
    """)
    graph.query("""
        MERGE (t1:Tag {name: '山景'})
        MERGE (t2:Tag {name: '湖景'})
        MERGE (t3:Tag {name: '森林'})
        MERGE (t4:Tag {name: '古村落'})
        MERGE (t5:Tag {name: '海岸线'})
        MERGE (t6:Tag {name: '城市漫步'})
        MERGE (t7:Tag {name: '日出'})
        MERGE (t8:Tag {name: '亲子友好'})
    """)


def close_falkordb():
    global _graph
    _graph = None

import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_database
from app.services.route_service import RouteService
from app.services.knowledge_service import KnowledgeService
from app.models.route import RouteCreate, DifficultyLevel


SEED_ROUTES = [
    {
        "name": "香山红叶步道",
        "city": "北京",
        "difficulty": "moderate",
        "distance_km": 8.5,
        "elevation_gain_m": 450,
        "elevation_loss_m": 440,
        "duration_hours": 3.5,
        "description": "北京最经典的赏秋徒步路线，沿途可欣赏满山红叶，登顶可俯瞰北京城全景。路线经过香炉峰、双清别墅等知名景点。",
        "tags": ["山景", "日出", "城市漫步"],
        "pois": ["香炉峰", "双清别墅", "碧云寺"],
    },
    {
        "name": "西湖环湖徒步",
        "city": "杭州",
        "difficulty": "easy",
        "distance_km": 15.2,
        "elevation_gain_m": 50,
        "elevation_loss_m": 50,
        "duration_hours": 4.0,
        "description": "环绕西湖的经典徒步路线，途经断桥、苏堤、雷峰塔、花港观鱼等著名景点，适合亲子出行和休闲徒步。",
        "tags": ["湖景", "亲子友好", "城市漫步"],
        "pois": ["断桥残雪", "苏堤春晓", "雷峰塔", "花港观鱼", "三潭印月"],
    },
    {
        "name": "青城山后山穿越",
        "city": "成都",
        "difficulty": "hard",
        "distance_km": 18.5,
        "elevation_gain_m": 850,
        "elevation_loss_m": 820,
        "duration_hours": 7.0,
        "description": "青城山后山穿越路线，沿途溪流瀑布、原始森林，风景秀丽但强度较大，需要一定体能基础。",
        "tags": ["山景", "森林"],
        "pois": ["泰安古镇", "五龙沟", "又一村", "白云寺"],
    },
    {
        "name": "深圳大梅沙海岸线",
        "city": "深圳",
        "difficulty": "moderate",
        "distance_km": 12.0,
        "elevation_gain_m": 300,
        "elevation_loss_m": 300,
        "duration_hours": 5.0,
        "description": "从大梅沙到小梅沙的海岸线徒步路线，沿途可欣赏壮丽海景，部分路段需要攀爬礁石，趣味性十足。",
        "tags": ["海岸线", "日出"],
        "pois": ["大梅沙海滨公园", "背仔角", "小梅沙"],
    },
    {
        "name": "外滩-陆家嘴城市漫步",
        "city": "上海",
        "difficulty": "easy",
        "distance_km": 6.5,
        "elevation_gain_m": 10,
        "elevation_loss_m": 10,
        "duration_hours": 2.5,
        "description": "从外滩沿黄浦江漫步至陆家嘴，欣赏上海经典天际线，途经南京路、东方明珠等地标建筑。",
        "tags": ["城市漫步", "亲子友好"],
        "pois": ["外滩", "南京路步行街", "东方明珠", "陆家嘴中心绿地"],
    },
    {
        "name": "灵隐寺-北高峰登山",
        "city": "杭州",
        "difficulty": "moderate",
        "distance_km": 8.0,
        "elevation_gain_m": 350,
        "elevation_loss_m": 350,
        "duration_hours": 3.5,
        "description": "从灵隐寺出发登顶北高峰，沿途古木参天、寺庙幽静，登顶后可俯瞰西湖全景。",
        "tags": ["山景", "古村落"],
        "pois": ["灵隐寺", "飞来峰", "北高峰", "韬光寺"],
    },
]


async def seed_routes():
    from datetime import datetime

    db = await get_database()
    collection = db.routes

    existing = await collection.count_documents({})
    if existing > 0:
        print(f"已有 {existing} 条路线数据，跳过种子数据插入")
        return

    for route_data in SEED_ROUTES:
        doc = dict(route_data)
        doc["difficulty"] = doc["difficulty"]
        doc["created_at"] = datetime.utcnow()
        doc["updated_at"] = datetime.utcnow()
        doc["gpx_points"] = []
        doc["cover_image"] = None
        await collection.insert_one(doc)
        print(f"  [OK] 插入路线: {doc['name']}")

    print(f"\n[OK] 成功插入 {len(SEED_ROUTES)} 条路线数据")


async def seed_knowledge_graph():
    from app.core.graph_db import get_falkordb_graph

    graph = get_falkordb_graph()

    for route_data in SEED_ROUTES:
        route_name = route_data["name"]
        city = route_data["city"]
        tags = route_data["tags"]
        pois = route_data["pois"]
        difficulty = route_data["difficulty"]
        distance = route_data["distance_km"]

        query = """
        MERGE (r:Route {name: $route_name})
        SET r.difficulty = $difficulty, r.distance_km = $distance
        MERGE (c:City {name: $city})
        MERGE (r)-[:LOCATED_IN]->(c)
        """
        graph.query(query, params={
            "route_name": route_name,
            "city": city,
            "difficulty": difficulty,
            "distance": distance,
        })

        for tag in tags:
            tag_query = """
            MERGE (t:Tag {name: $tag})
            MERGE (r:Route {name: $route_name})
            MERGE (r)-[:TAGGED]->(t)
            """
            graph.query(tag_query, params={"tag": tag, "route_name": route_name})

        for poi in pois:
            poi_query = """
            MERGE (p:POI {name: $poi})
            MERGE (r:Route {name: $route_name})
            MERGE (r)-[:CONTAINS]->(p)
            """
            graph.query(poi_query, params={"poi": poi, "route_name": route_name})

        print(f"  [OK] 写入知识图谱: {route_name}")

    print(f"\n[OK] 成功写入 {len(SEED_ROUTES)} 条路线到知识图谱")


async def main():
    print("[Seed] 开始种子数据初始化...\n")

    print("--- MongoDB 路线数据 ---")
    await seed_routes()

    print("\n--- FalkorDB 知识图谱 ---")
    await seed_knowledge_graph()

    print("\n[Done] 种子数据初始化完成！")


if __name__ == "__main__":
    asyncio.run(main())

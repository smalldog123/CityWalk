import asyncio
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_database
from app.services.route_service import RouteService
from app.services.knowledge_service import KnowledgeService
from app.models.route import RouteCreate, DifficultyLevel


def _build_gpx(lat_start, lng_start, ele_start, waypoints):
    points = []
    start = datetime(2024, 10, 1, 8, 0, 0)
    for i, (d_lat, d_lng, d_ele) in enumerate(waypoints):
        points.append({
            "lat": round(lat_start + d_lat, 6),
            "lng": round(lng_start + d_lng, 6),
            "elevation": ele_start + d_ele,
            "timestamp": start + timedelta(minutes=i * 8),
        })
    return points


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
        "gpx_lat": 39.9920,
        "gpx_lng": 116.1865,
        "gpx_ele": 100,
        "gpx_waypoints": [
            (0.0000, 0.0000, 10), (0.0008, -0.0003, 30), (0.0015, -0.0005, 50),
            (0.0022, -0.0009, 65), (0.0030, -0.0012, 80), (0.0037, -0.0010, 95),
            (0.0042, -0.0015, 110), (0.0048, -0.0018, 135), (0.0052, -0.0016, 155),
            (0.0056, -0.0019, 170), (0.0059, -0.0015, 190), (0.0060, -0.0012, 210),
            (0.0059, -0.0008, 235), (0.0056, -0.0005, 260), (0.0054, -0.0003, 285),
            (0.0051, -0.0001, 310), (0.0047, 0.0002, 340), (0.0044, 0.0000, 370),
            (0.0040, 0.0003, 400), (0.0039, 0.0005, 430), (0.0038, 0.0003, 445),
            (0.0036, 0.0006, 455), (0.0035, 0.0004, 450), (0.0033, 0.0006, 445),
            (0.0035, 0.0002, 460), (0.0035, 0.0000, 455),
        ],
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
        "gpx_lat": 30.2545,
        "gpx_lng": 120.1610,
        "gpx_ele": 10,
        "gpx_waypoints": [
            (0.0000, 0.0000, 0), (0.0010, -0.0005, 0), (0.0025, -0.0010, -2),
            (0.0045, -0.0015, 1), (0.0065, -0.0010, 0), (0.0085, 0.0000, 2),
            (0.0100, 0.0020, 3), (0.0110, 0.0040, 0), (0.0115, 0.0070, -1),
            (0.0110, 0.0100, 0), (0.0100, 0.0130, 2), (0.0080, 0.0160, 1),
            (0.0060, 0.0180, 0), (0.0035, 0.0195, 2), (0.0010, 0.0200, 0),
            (-0.0015, 0.0195, 1), (-0.0035, 0.0180, -2), (-0.0055, 0.0160, 0),
            (-0.0065, 0.0135, 2), (-0.0070, 0.0110, 1), (-0.0065, 0.0080, 0),
            (-0.0055, 0.0060, -1), (-0.0040, 0.0040, 0), (-0.0025, 0.0025, 2),
            (-0.0010, 0.0010, 1), (0.0000, 0.0000, 0),
        ],
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
        "gpx_lat": 30.9260,
        "gpx_lng": 103.5460,
        "gpx_ele": 680,
        "gpx_waypoints": [
            (0.0000, 0.0000, 10), (0.0010, 0.0010, 30), (0.0022, 0.0008, 55),
            (0.0035, 0.0015, 80), (0.0048, 0.0012, 110), (0.0060, 0.0018, 140),
            (0.0072, 0.0022, 175), (0.0083, 0.0020, 210), (0.0093, 0.0025, 250),
            (0.0102, 0.0023, 295), (0.0108, 0.0028, 340), (0.0115, 0.0025, 390),
            (0.0120, 0.0030, 440), (0.0128, 0.0028, 500), (0.0135, 0.0032, 560),
            (0.0140, 0.0030, 615), (0.0145, 0.0033, 670), (0.0152, 0.0030, 730),
            (0.0158, 0.0035, 780), (0.0162, 0.0032, 820), (0.0165, 0.0035, 850),
            (0.0160, 0.0032, 830), (0.0155, 0.0035, 810), (0.0148, 0.0032, 780),
            (0.0142, 0.0035, 745), (0.0135, 0.0030, 710), (0.0128, 0.0035, 680),
        ],
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
        "gpx_lat": 22.5980,
        "gpx_lng": 114.3110,
        "gpx_ele": 5,
        "gpx_waypoints": [
            (0.0000, 0.0000, 0), (0.0008, 0.0015, 3), (0.0012, 0.0035, 8),
            (0.0018, 0.0055, 15), (0.0020, 0.0080, 10), (0.0028, 0.0100, 20),
            (0.0030, 0.0125, 8), (0.0035, 0.0150, 25), (0.0038, 0.0175, 15),
            (0.0045, 0.0195, 30), (0.0042, 0.0220, 12), (0.0050, 0.0245, 35),
            (0.0055, 0.0270, 18), (0.0058, 0.0295, 28), (0.0065, 0.0320, 10),
            (0.0070, 0.0345, 22), (0.0075, 0.0365, 8), (0.0082, 0.0390, 20),
            (0.0085, 0.0415, 5), (0.0090, 0.0440, 15), (0.0095, 0.0465, 25),
            (0.0102, 0.0490, 10), (0.0108, 0.0515, 18), (0.0112, 0.0535, 5),
            (0.0118, 0.0560, 8),
        ],
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
        "gpx_lat": 31.2380,
        "gpx_lng": 121.4850,
        "gpx_ele": 3,
        "gpx_waypoints": [
            (0.0000, 0.0000, 0), (0.0010, 0.0010, 1), (0.0020, 0.0020, 0),
            (0.0035, 0.0015, 2), (0.0050, 0.0025, 1), (0.0065, 0.0030, 0),
            (0.0080, 0.0020, 1), (0.0090, 0.0015, 2), (0.0100, 0.0025, 0),
            (0.0105, 0.0035, 1), (0.0100, 0.0050, 0), (0.0090, 0.0065, 2),
            (0.0075, 0.0075, 1), (0.0060, 0.0085, 0), (0.0040, 0.0095, 2),
            (0.0020, 0.0085, 1), (0.0000, 0.0075, 0), (-0.0010, 0.0065, 1),
            (-0.0020, 0.0050, 2), (-0.0030, 0.0040, 0), (-0.0025, 0.0030, 1),
            (-0.0015, 0.0020, 0), (-0.0005, 0.0010, 2), (0.0000, 0.0000, 0),
        ],
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
        "gpx_lat": 30.2410,
        "gpx_lng": 120.1030,
        "gpx_ele": 30,
        "gpx_waypoints": [
            (0.0000, 0.0000, 0), (0.0008, 0.0005, 15), (0.0015, 0.0010, 30),
            (0.0022, 0.0006, 45), (0.0030, 0.0012, 60), (0.0038, 0.0008, 80),
            (0.0045, 0.0015, 95), (0.0052, 0.0010, 115), (0.0058, 0.0015, 140),
            (0.0065, 0.0012, 165), (0.0070, 0.0016, 190), (0.0075, 0.0013, 215),
            (0.0080, 0.0018, 240), (0.0085, 0.0015, 265), (0.0090, 0.0019, 290),
            (0.0095, 0.0016, 310), (0.0100, 0.0020, 330), (0.0102, 0.0018, 345),
            (0.0105, 0.0020, 355), (0.0102, 0.0018, 350), (0.0098, 0.0019, 340),
            (0.0095, 0.0016, 320), (0.0090, 0.0015, 300), (0.0085, 0.0013, 280),
            (0.0080, 0.0012, 255), (0.0075, 0.0010, 230), (0.0070, 0.0008, 205),
        ],
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
        doc["gpx_points"] = _build_gpx(
            doc.pop("gpx_lat"), doc.pop("gpx_lng"),
            doc.pop("gpx_ele"), doc.pop("gpx_waypoints"),
        )
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

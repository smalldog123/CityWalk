from __future__ import annotations
from app.core.graph_db import get_falkordb_graph
from typing import Optional


class KnowledgeService:
    def __init__(self):
        self._graph = None

    def _get_graph(self):
        if self._graph is None:
            self._graph = get_falkordb_graph()
        return self._graph

    async def search_by_entity(self, entity_type: str, name: str) -> list[dict]:
        graph = self._get_graph()
        allowed_labels = {"Route", "POI", "Tag", "City"}
        label = entity_type.capitalize()
        if label not in allowed_labels:
            label = "Route"
        query = f"""
        MATCH (e:{label})
        WHERE e.name CONTAINS $name
        OPTIONAL MATCH (e)-[r]-(related)
        RETURN e, type(r) AS rel_type, labels(related) AS related_labels, related
        LIMIT 20
        """
        result = graph.query(query, params={"name": name})
        return self._parse_result(result)

    async def search_routes_by_city(self, city_name: str) -> list[dict]:
        graph = self._get_graph()
        query = """
        MATCH (c:City {name: $city})-[:LOCATED_IN]-(r:Route)
        OPTIONAL MATCH (r)-[:TAGGED]->(t:Tag)
        OPTIONAL MATCH (r)-[:CONTAINS]->(p:POI)
        RETURN r, collect(DISTINCT t) AS tags, collect(DISTINCT p) AS pois
        LIMIT 20
        """
        result = graph.query(query, params={"city": city_name})
        return self._parse_result(result)

    async def search_routes_by_tag(self, tag_name: str) -> list[dict]:
        graph = self._get_graph()
        query = """
        MATCH (t:Tag)-[:TAGGED]-(r:Route)
        WHERE t.name CONTAINS $tag
        OPTIONAL MATCH (r)-[:LOCATED_IN]->(c:City)
        RETURN r, c
        LIMIT 20
        """
        result = graph.query(query, params={"tag": tag_name})
        return self._parse_result(result)

    async def search_poi_near_route(self, route_name: str) -> list[dict]:
        graph = self._get_graph()
        query = """
        MATCH (r:Route)-[:CONTAINS]->(p:POI)
        WHERE r.name CONTAINS $route
        RETURN r, collect(p) AS pois
        LIMIT 10
        """
        result = graph.query(query, params={"route": route_name})
        return self._parse_result(result)

    async def semantic_search(self, query_text: str) -> list[dict]:
        graph = self._get_graph()
        keywords = query_text.split()
        conditions = []
        params = {}
        for i, kw in enumerate(keywords):
            param_name = f"kw_{i}"
            conditions.append(f"e.name CONTAINS ${param_name}")
            params[param_name] = kw
        where_clause = " OR ".join(conditions)

        query = f"""
        MATCH (e)
        WHERE {where_clause}
        OPTIONAL MATCH (e)-[r]-(related)
        RETURN e, type(r) AS rel_type, labels(related) AS related_labels, related
        LIMIT 30
        """
        result = graph.query(query, params=params)
        return self._parse_result(result)

    async def add_route_to_graph(self, route_data: dict):
        graph = self._get_graph()
        route_name = route_data.get("name", "")
        city = route_data.get("city", "")
        tags = route_data.get("tags", [])
        pois = route_data.get("pois", [])
        difficulty = route_data.get("difficulty", "")
        distance = route_data.get("distance_km", 0)

        query = f"""
        MERGE (r:Route {{name: $route_name}})
        SET r.difficulty = $difficulty, r.distance_km = $distance
        MERGE (c:City {{name: $city}})
        MERGE (r)-[:LOCATED_IN]->(c)
        """
        params = {
            "route_name": route_name,
            "city": city,
            "difficulty": difficulty,
            "distance": distance,
        }
        graph.query(query, params=params)

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

    def _parse_result(self, result) -> list[dict]:
        records = []
        if result is None:
            return records
        for row in result.result_set:
            record = {}
            for i, header in enumerate(result.header):
                if i < len(row):
                    val = row[i]
                    if hasattr(val, "properties"):
                        record[header] = dict(val.properties)
                    elif isinstance(val, list):
                        record[header] = [
                            dict(v.properties) if hasattr(v, "properties") else v
                            for v in val
                        ]
                    else:
                        record[header] = val
            records.append(record)
        return records

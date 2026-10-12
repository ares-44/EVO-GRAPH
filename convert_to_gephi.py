import json
from pathlib import Path
from xml.etree.ElementTree import Element, SubElement, ElementTree, register_namespace

# ============================================================
# EVO-GRAPH -> GEXF converter for Gephi
# Does NOT modify app.py or evo_graph.json.
# ============================================================

ROOT = Path(__file__).resolve().parent
INPUT = ROOT / "data" / "evo_graph.json"
OUTPUT = ROOT / "evo_graph.gexf"

GEXF_NS = "http://gexf.net/1.3"
VIZ_NS = "http://gexf.net/1.3/viz"

register_namespace("", GEXF_NS)
register_namespace("viz", VIZ_NS)


def safe_text(value):
    if value is None:
        return ""
    return str(value)


def xml_tag(name):
    return f"{{{GEXF_NS}}}{name}"


def viz_tag(name):
    return f"{{{VIZ_NS}}}{name}"


def main():
    if not INPUT.exists():
        raise FileNotFoundError(
            f"Graph file not found:\n{INPUT}\n\n"
            "Run this script from the EVO GRAPH project folder."
        )

    with INPUT.open("r", encoding="utf-8") as f:
        data = json.load(f)

    nodes = data.get("nodes", [])
    edges = data.get(
        "relationships",
        data.get("edges", data.get("links", [])),
    )

    # Root
    gexf = Element(
        xml_tag("gexf"),
        {
            "version": "1.3",
            f"{{http://www.w3.org/2001/XMLSchema-instance}}schemaLocation":
                f"{GEXF_NS} http://gexf.net/1.3/gexf.xsd",
        },
    )

    # Metadata
    meta = SubElement(
        gexf,
        xml_tag("meta"),
        {"lastmodifieddate": "2026-10-08"},
    )
    SubElement(meta, xml_tag("creator")).text = "EVO-GRAPH"
    SubElement(meta, xml_tag("description")).text = (
        "EVO-GRAPH dynamic Skill-Experience Knowledge Graph"
    )

    graph = SubElement(
        gexf,
        xml_tag("graph"),
        {
            "mode": "static",
            "defaultedgetype": "directed",
            "idtype": "string",
        },
    )

    # Node attributes that are useful in Gephi's Data Laboratory.
    node_attributes = SubElement(
        graph,
        xml_tag("attributes"),
        {"class": "node"},
    )

    SubElement(
        node_attributes,
        xml_tag("attribute"),
        {"id": "type", "title": "Type", "type": "string"},
    )
    SubElement(
        node_attributes,
        xml_tag("attribute"),
        {"id": "name", "title": "Name", "type": "string"},
    )

    edge_attributes = SubElement(
        graph,
        xml_tag("attributes"),
        {"class": "edge"},
    )

    SubElement(
        edge_attributes,
        xml_tag("attribute"),
        {"id": "relationship", "title": "Relationship", "type": "string"},
    )

    # Nodes
    nodes_element = SubElement(
        graph,
        xml_tag("nodes"),
        {"count": str(len(nodes))},
    )

    color_map = {
        "SKILL": (24, 174, 234),
        "TOPIC": (155, 89, 255),
        "EXPERIENCE": (40, 201, 148),
        "OTHER": (124, 141, 163),
    }

    node_ids = set()

    for node in nodes:
        node_id = safe_text(node.get("id"))
        if not node_id:
            continue

        node_ids.add(node_id)

        node_type = safe_text(node.get("type", "OTHER")).upper()
        node_name = safe_text(node.get("name", node_id))

        gephi_node = SubElement(
            nodes_element,
            xml_tag("node"),
            {
                "id": node_id,
                "label": node_name,
            },
        )

        attvalues = SubElement(gephi_node, xml_tag("attvalues"))

        SubElement(
            attvalues,
            xml_tag("attvalue"),
            {"for": "type", "value": node_type},
        )
        SubElement(
            attvalues,
            xml_tag("attvalue"),
            {"for": "name", "value": node_name},
        )

        r, g, b = color_map.get(node_type, color_map["OTHER"])
        SubElement(
            gephi_node,
            viz_tag("color"),
            {"r": str(r), "g": str(g), "b": str(b), "a": "1.0"},
        )

        SubElement(
            gephi_node,
            viz_tag("size"),
            {"value": "10"},
        )

    # Edges
    edges_element = SubElement(
        graph,
        xml_tag("edges"),
        {"count": str(len(edges))},
    )

    valid_edges = 0

    for index, edge in enumerate(edges):
        source = safe_text(edge.get("source", edge.get("from")))
        target = safe_text(edge.get("target", edge.get("to")))

        if not source or not target:
            continue

        # Keep only edges whose endpoints exist.
        if source not in node_ids or target not in node_ids:
            continue

        relationship = safe_text(
            edge.get("relationship", edge.get("label", "RELATED_TO"))
        )

        gephi_edge = SubElement(
            edges_element,
            xml_tag("edge"),
            {
                "id": f"e{index}",
                "source": source,
                "target": target,
            },
        )

        attvalues = SubElement(gephi_edge, xml_tag("attvalues"))
        SubElement(
            attvalues,
            xml_tag("attvalue"),
            {"for": "relationship", "value": relationship},
        )

        valid_edges += 1

    # Pretty indentation on Python 3.9+
    try:
        ElementTree.indent(gexf, space="  ")
    except AttributeError:
        pass

    ElementTree(gexf).write(
        OUTPUT,
        encoding="utf-8",
        xml_declaration=True,
    )

    print("=" * 60)
    print("EVO-GRAPH -> GEXF conversion complete")
    print("=" * 60)
    print(f"Nodes written : {len(node_ids)}")
    print(f"Edges written : {valid_edges}")
    print(f"Output       : {OUTPUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()

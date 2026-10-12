import json



import re

import unicodedata

import json as _json

import requests



import networkx as nx











class EvoGraph:







    STOP_WORDS = {



        "a", "an", "the", "is", "are", "was", "were",



        "what", "why", "how", "do", "does", "did",



        "i", "you", "we", "they", "it", "this", "that",



        "to", "of", "in", "on", "for", "and", "or",



        "with", "use", "used", "using", "can", "be",



        "as", "by", "from", "into", "than", "then",



        "would", "should", "could"



    }







    def __init__(self):



        self.graph = nx.DiGraph()







    # ==========================================



    # TEXT PROCESSING



    # ==========================================







    def tokenize(self, text):







        words = re.findall(



            r"[a-zA-Z0-9+#]+",



            text.lower()



        )







        return {



            word



            for word in words



            if word not in self.STOP_WORDS



            and len(word) > 1



        }







    # ==========================================



    # ADD NODE



    # ==========================================







    def add_node(



        self,



        node_id,



        node_type,



        name



    ):







        self.graph.add_node(



            node_id,



            type=node_type,



            name=name



        )







    # ==========================================



    # ADD RELATIONSHIP



    # ==========================================







    def add_relationship(



        self,



        source,



        relationship,



        target



    ):







        self.graph.add_edge(



            source,



            target,



            relationship=relationship



        )







    # ==========================================



    # ==========================================

    # AUTOMATIC CONCEPT DISCOVERY

    # ==========================================



    def _discover_structure_with_ollama(self, text):

        """Use local Qwen to extract graph concepts from a new experience."""

        prompt = f"""You are the graph-structure extractor for EVO-GRAPH.

Extract a small useful knowledge graph from the technical interaction below.

Do not invent unrelated concepts. Prefer 1-3 skills, 1-4 topics, and 1-5 concepts.

Return ONLY valid JSON with exactly these keys:

{{

  "skills": [{{"name": "...", "description": "..."}}],

  "topics": [{{"name": "...", "description": "..."}}],

  "concepts": [{{"name": "...", "description": "..."}}]

}}



Interaction:

{text[:8000]}

"""

        response = requests.post(

            "http\://localhost:11434/api/generate",

            json={"model": "qwen2.5:3b", "prompt": prompt, "stream": False, "format": "json"},

            timeout=45,

        )

        response.raise_for_status()

        raw = response.json().get("response", "").strip()

        data = _json.loads(raw)

        return data if isinstance(data, dict) else {}



    def _fallback_structure(self, text):

        """Conservative fallback when the local model is unavailable."""

        tokens = sorted(self.tokenize(text))

        common = {

            "python", "sql", "database", "data", "structure", "algorithm",

            "machine", "learning", "ai", "cloud", "network", "security",

            "programming", "debugging", "stack", "queue", "linked", "list",

        }

        hits = [t for t in tokens if t in common]

        topics = []

        if "stack" in hits and "linked" in hits:

            topics.append({"name": "Stack and Linked List", "description": "Comparison of data structures."})

        elif hits:

            topics.append({"name": hits[0].title(), "description": "Automatically detected topic."})

        skills = []

        if "python" in hits:

            skills.append({"name": "Python Programming", "description": "Python programming and problem solving."})

        elif "sql" in hits or "database" in hits:

            skills.append({"name": "Database Programming", "description": "Working with databases and SQL."})

        elif "algorithm" in hits or "structure" in hits:

            skills.append({"name": "Data Structures and Algorithms", "description": "Algorithmic and data-structure problem solving."})

        concepts = [{"name": t.title(), "description": "Detected technical concept."} for t in hits[:4]]

        return {"skills": skills, "topics": topics, "concepts": concepts}



    def discover_and_attach(self, experience_id, text):

        """Discover and attach a rich structure for a newly learned experience."""

        try:

            structure = self._discover_structure_with_ollama(text)

            source = "ollama"

        except Exception as error:

            print(f"⚠️ Dynamic graph discovery fallback: {error}")

            structure = self._fallback_structure(text)

            source = "fallback"

        result = self.add_discovered_structure(

            experience_id,

            skills=structure.get("skills", []),

            topics=structure.get("topics", []),

            concepts=structure.get("concepts", []),

        )

        node = self.graph.nodes.get(experience_id)

        if node is not None:

            node["graph_discovery"] = source

            node["discovered_skills"] = result["skills"]

            node["discovered_topics"] = result["topics"]

            node["discovered_concepts"] = result["concepts"]

        return result



    # ADD EXPERIENCE



    # ==========================================







    def add_experience(



        self,



        experience_id,



        experience,



        skill_id=None,



        confidence=0.5,



        validated=False



    ):







        self.graph.add_node(



            experience_id,



            type="EXPERIENCE",



            name=experience,



            experience=experience,



            confidence=confidence,



            validated=validated,



            feedback_count=0



        )



        # Automatically discover a new skill/topic/concept neighborhood.

        try:

            self.discover_and_attach(experience_id, experience)

        except Exception as error:

            print(f"⚠️ Dynamic graph attachment skipped: {error}")







        if skill_id and skill_id in self.graph.nodes:

            self.graph.add_edge(



                experience_id,



                skill_id,



                relationship="IMPROVES"



            )







    # ==========================================



    # ==========================================

    # DYNAMIC GRAPH DISCOVERY / UPSERT

    # ==========================================



    @staticmethod

    def _slugify(value):

        value = unicodedata.normalize("NFKD", str(value or ""))

        value = value.encode("ascii", "ignore").decode("ascii")

        value = re.sub(r"[^a-zA-Z0-9]+", "_", value.lower()).strip("_")

        return value[:60] or "unknown"



    def _find_named_node(self, node_type, name):

        target = self._slugify(name)

        for node_id, data in self.graph.nodes(data=True):

            if str(data.get("type", "")).upper() != node_type.upper():

                continue

            if self._slugify(data.get("name", node_id)) == target:

                return node_id

        return None



    def upsert_concept_node(self, node_type, name, description=""):

        node_type = str(node_type).upper().strip()

        name = str(name or "").strip()

        if node_type not in {"SKILL", "TOPIC", "CONCEPT"} or not name:

            return None

        existing = self._find_named_node(node_type, name)

        if existing:

            node = self.graph.nodes[existing]

            node["discovered"] = True

            node["discovery_count"] = int(node.get("discovery_count", 0)) + 1

            if description and not node.get("description"):

                node["description"] = description

            return existing

        base_id = f"{node_type.lower()}_{self._slugify(name)}"

        node_id = base_id

        counter = 2

        while node_id in self.graph.nodes:

            node_id = f"{base_id}_{counter}"

            counter += 1

        self.graph.add_node(node_id, type=node_type, name=name, description=description, discovered=True, discovery_count=1)

        return node_id



    def add_discovered_structure(self, experience_id, skills=None, topics=None, concepts=None, relationships=None):

        if experience_id not in self.graph.nodes:

            return {"skills": [], "topics": [], "concepts": [], "relationships": 0}

        skills, topics, concepts, relationships = skills or [], topics or [], concepts or [], relationships or []

        result = {"skills": [], "topics": [], "concepts": [], "relationships": 0}

        skill_ids, topic_ids, concept_ids = [], [], []

        for item in skills:

            name = item.get("name") if isinstance(item, dict) else item

            desc = item.get("description", "") if isinstance(item, dict) else ""

            nid = self.upsert_concept_node("SKILL", name, desc)

            if nid:

                skill_ids.append(nid); result["skills"].append(nid)

                self.add_relationship(experience_id, "BUILDS", nid); result["relationships"] += 1

        for item in topics:

            name = item.get("name") if isinstance(item, dict) else item

            desc = item.get("description", "") if isinstance(item, dict) else ""

            nid = self.upsert_concept_node("TOPIC", name, desc)

            if nid:

                topic_ids.append(nid); result["topics"].append(nid)

                self.add_relationship(experience_id, "APPLIES_TO", nid); result["relationships"] += 1

        for item in concepts:

            name = item.get("name") if isinstance(item, dict) else item

            desc = item.get("description", "") if isinstance(item, dict) else ""

            nid = self.upsert_concept_node("CONCEPT", name, desc)

            if nid:

                concept_ids.append(nid); result["concepts"].append(nid)

                self.add_relationship(experience_id, "MENTIONS", nid); result["relationships"] += 1

        for topic in topic_ids:

            for skill in skill_ids:

                self.add_relationship(topic, "PART_OF", skill); result["relationships"] += 1

        for concept in concept_ids:

            for topic in topic_ids:

                self.add_relationship(concept, "RELATED_TO", topic); result["relationships"] += 1

        for i, left in enumerate(topic_ids):

            for right in topic_ids[i + 1:]:

                self.add_relationship(left, "RELATED_TO", right)

                self.add_relationship(right, "RELATED_TO", left)

                result["relationships"] += 2

        return result



    def get_experience_context_nodes(self, experience_id):

        if experience_id not in self.graph.nodes:

            return []

        return [

            self.graph.nodes[target].get("name", target)

            for target in self.graph.successors(experience_id)

            if str(self.graph.nodes[target].get("type", "")).upper() in {"SKILL", "TOPIC", "CONCEPT"}

        ]



    # UPDATE EXPERIENCE



    # ==========================================







    def update_experience(



        self,



        experience_id,



        feedback



    ):







        if experience_id not in self.graph.nodes:







            return False







        node = self.graph.nodes[



            experience_id



        ]







        confidence = node.get(



            "confidence",



            0.5



        )







        feedback_count = node.get(



            "feedback_count",



            0



        )







        feedback_count += 1







        if feedback == "positive":







            confidence = min(



                1.0,



                confidence + 0.1



            )







            validated = True







        elif feedback == "negative":







            confidence = max(



                0.0,



                confidence - 0.2



            )







            validated = confidence >= 0.4







        else:







            validated = node.get(



                "validated",



                False



            )







        node["confidence"] = confidence



        node["validated"] = validated



        node["feedback_count"] = feedback_count







        return True







    # ==========================================



    # EXPERIENCE SKILL



    # ==========================================







    def get_experience_skill(



        self,



        experience_id



    ):







        skills = []







        for target in self.graph.successors(



            experience_id



        ):







            edge = self.graph[



                experience_id



            ][target]







            if (



                edge.get("relationship")



                == "IMPROVES"



            ):







                node = self.graph.nodes[



                    target



                ]







                skills.append(



                    node.get(



                        "name",



                        target



                    )



                )







        return skills







    # ==========================================



    # SEARCH EXPERIENCES



    # ==========================================







    def search_experiences(

        self,

        query,

        limit=3,

        validated_only=False,

        min_score=0.10

    ):

        """Retrieve experiences using true semantic similarity + graph metadata.



        Primary retrieval uses SentenceTransformer embeddings with FAISS cosine

        similarity. If the optional semantic dependencies are unavailable, the

        original lexical retrieval logic is used as a safe fallback.

        """

        query = str(query or "").strip()

        if not query:

            return []



        candidates = []

        for node_id, data in self.graph.nodes(data=True):

            if str(data.get("type", "")).upper() != "EXPERIENCE":

                continue

            if validated_only and not data.get("validated", False):

                continue



            experience = str(data.get("experience", data.get("name", "")) or "")

            source_question = str(data.get("source_question", "") or "")

            name = str(data.get("name", "") or "")

            if not experience and not source_question and not name:

                continue



            skills = self.get_experience_skill(node_id)

            context_nodes = self.get_experience_context_nodes(node_id)

            searchable = " ".join([source_question, experience, name] + [str(x) for x in skills] + [str(x) for x in context_nodes])

            candidates.append((node_id, data, searchable, skills))



        if not candidates:

            return []



        # ------------------------------------------------------------

        # TRUE SEMANTIC RETRIEVAL: SentenceTransformer + FAISS

        # ------------------------------------------------------------

        try:

            import numpy as np

            import faiss

            from sentence_transformers import SentenceTransformer



            model_name = "all-MiniLM-L6-v2"

            model = getattr(self, "_semantic_model", None)

            if model is None:

                model = SentenceTransformer(model_name)

                self._semantic_model = model



            texts = [item[2] for item in candidates]
            # Cache the expensive document embeddings and FAISS index. The cache
            # is invalidated only when the searchable experience content/order changes.
            # Feedback/confidence metadata can change without re-embedding documents.
            cache_key = tuple((str(item[0]), item[2]) for item in candidates)
            cache_key = (model_name, cache_key)
            cached_key = getattr(self, "_semantic_cache_key", None)
            cached_index = getattr(self, "_semantic_faiss_index", None)
            cached_embeddings = getattr(self, "_semantic_embeddings", None)

            if cached_key != cache_key or cached_index is None or cached_embeddings is None:
                embeddings = model.encode(
                    texts,
                    batch_size=64,
                    normalize_embeddings=True,
                    convert_to_numpy=True,
                    show_progress_bar=False,
                ).astype("float32")
                index = faiss.IndexFlatIP(embeddings.shape[1])
                index.add(embeddings)
                self._semantic_cache_key = cache_key
                self._semantic_embeddings = embeddings
                self._semantic_faiss_index = index
            else:
                embeddings = cached_embeddings
                index = cached_index

            query_embedding = model.encode(
                [query],
                normalize_embeddings=True,
                convert_to_numpy=True,
                show_progress_bar=False,
            ).astype("float32")

            k = min(len(candidates), max(limit * 5, 10))
            distances, indices = index.search(query_embedding, k)

            results = []

            for raw_score, idx in zip(distances[0], indices[0]):

                if idx < 0:

                    continue

                node_id, data, searchable, skills = candidates[int(idx)]

                semantic_score = float(max(0.0, min(1.0, raw_score)))



                confidence = float(data.get("confidence", 0.0) or 0.0)

                validated = bool(data.get("validated", False))

                feedback_count = int(data.get("feedback_count", 0) or 0)



                # Graph-aware metadata score. This rewards trusted experiences

                # without overpowering semantic relevance.

                validation_score = 1.0 if validated else 0.0

                feedback_score = min(feedback_count / 5.0, 1.0)

                graph_score = (

                    0.50 * confidence

                    + 0.30 * validation_score

                    + 0.20 * feedback_score

                )



                final_score = (

                    0.70 * semantic_score

                    + 0.20 * graph_score

                    + 0.10 * confidence

                )



                if final_score < min_score:

                    continue



                results.append({

                    "id": node_id,

                    "experience": data.get("experience", data.get("name", "")),

                    "description": data.get("description", ""),

                    "semantic_score": round(semantic_score, 4),

                    "text_score": round(semantic_score, 4),

                    "graph_score": round(graph_score, 4),

                    "score": round(final_score, 4),

                    "final_score": round(final_score, 4),

                    "confidence": confidence,

                    "validated": validated,

                    "feedback_count": feedback_count,

                    "feedback_type": data.get("feedback_type"),

                    "source_question": data.get("source_question", ""),

                    "source_answer": data.get("source_answer", ""),

                    "graph_context": self.get_experience_context_nodes(node_id),

                })



            results.sort(

                key=lambda x: (x["score"], x["confidence"], x["feedback_count"]),

                reverse=True,

            )

            return results[:limit]



        except Exception as semantic_error:

            # Keep EVO-GRAPH usable if the embedding stack is unavailable.

            print(f"⚠️ Semantic retrieval unavailable; using lexical fallback: {semantic_error}")



        # ------------------------------------------------------------

        # SAFE FALLBACK: original lexical retrieval

        # ------------------------------------------------------------

        query_tokens = self.tokenize(query)

        if not query_tokens:

            return []



        fallback = []

        query_clean = " ".join(query.lower().split())

        for node_id, data, searchable, skills in candidates:

            experience_tokens = self.tokenize(searchable)

            if not experience_tokens:

                continue



            overlap = query_tokens & experience_tokens

            if not overlap:

                continue



            union = query_tokens | experience_tokens

            jaccard = len(overlap) / len(union) if union else 0.0

            coverage = len(overlap) / len(query_tokens) if query_tokens else 0.0

            experience_clean = " ".join(searchable.lower().split())

            phrase_bonus = 0.60 if query_clean in experience_clean else 0.0



            skill_tokens = set()

            for skill in skills:

                skill_tokens.update(self.tokenize(skill))

            skill_overlap = query_tokens & skill_tokens

            skill_score = len(skill_overlap) / len(query_tokens) if query_tokens else 0.0



            confidence = float(data.get("confidence", 0.0) or 0.0)

            validated = bool(data.get("validated", False))

            feedback_count = int(data.get("feedback_count", 0) or 0)

            score = (

                0.30 * jaccard

                + 0.35 * coverage

                + 0.10 * skill_score

                + 0.05 * confidence

                + phrase_bonus

            )

            if score < min_score:

                continue



            fallback.append({

                "id": node_id,

                "experience": data.get("experience", data.get("name", "")),

                "description": data.get("description", ""),

                "semantic_score": round(jaccard, 4),

                "text_score": round(jaccard, 4),

                "graph_score": round(skill_score, 4),

                "score": round(score, 4),

                "final_score": round(score, 4),

                "confidence": confidence,

                "validated": validated,

                "feedback_count": feedback_count,

                "feedback_type": data.get("feedback_type"),

                "source_question": data.get("source_question", ""),

                "source_answer": data.get("source_answer", ""),

                "graph_context": self.get_experience_context_nodes(node_id),

            })



        fallback.sort(

            key=lambda x: (x["score"], x["confidence"], x["feedback_count"]),

            reverse=True,

        )

        return fallback[:limit]



    def save_graph(



        self,



        path



    ):







        data = nx.node_link_data(



            self.graph



        )







        with open(



            path,



            "w",



            encoding="utf-8"



        ) as file:







            json.dump(



                data,



                file,



                indent=2



            )







        print(



            f"Graph saved to: {path}"



        )







    # ==========================================



    # LOAD GRAPH



    # ==========================================







    def load_graph(



        self,



        path



    ):







        with open(



            path,



            "r",



            encoding="utf-8"



        ) as file:







            data = json.load(file)







        self.graph = nx.node_link_graph(



            data,



            directed=True



        )







        print(



            f"Graph loaded from: {path}"



        )







    # ==========================================



    # SHOW GRAPH



    # ==========================================







    def show_graph(self):







        print("\n===== CURRENT GRAPH =====")







        print("\nNodes:")







        for node_id, data in self.graph.nodes(



            data=True



        ):







            node_type = data.get(



                "type",



                "UNKNOWN"



            )







            name = data.get(



                "name",



                ""



            )







            print(



                f"{node_id}: "



                f"{node_type} → {name}"



            )







            if node_type == "EXPERIENCE":







                print(



                    "   Confidence: "



                    f"{data.get('confidence', 0)}"



                )







                print(



                    "   Validated: "



                    f"{data.get('validated', False)}"



                )







                print(



                    "   Feedback count: "



                    f"{data.get('feedback_count', 0)}"



                )







        print("\nRelationships:")







        for source, target, data in self.graph.edges(



            data=True



        ):







            print(



                f"{source} "



                f"--[{data.get('relationship')}]--> "



                f"{target}"



            )











# ==========================================



# OFFLINE TEST



# ==========================================







if __name__ == "__main__":







    graph = EvoGraph()







    graph.add_node(



        "skill_python",



        "SKILL",



        "Python Programming"



    )







    graph.add_node(



        "topic_debugging",



        "TOPIC",



        "Python Debugging"



    )







    graph.add_experience(



        "experience_001",



        "Check Python error messages before changing code",



        "skill_python",



        confidence=0.8



    )







    graph.add_experience(



        "experience_002",



        "Use print statements to debug Python variables",



        "skill_python",



        confidence=0.6



    )







    print(



        "\n===== SEARCH TEST ====="



    )







    results = graph.search_experiences(



        "How should I debug a Python error?"



    )







    for result in results:







        print(



            f"\n{result['id']}"



        )







        print(



            f"Experience: "



            f"{result['experience']}"



        )







        print(



            f"Score: "



            f"{result['score']}"



        )







    graph.show_graph()

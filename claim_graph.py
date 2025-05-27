import networkx as nx
from typing import List, Dict, Any
import json
from datetime import datetime
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

class ClaimGraph:
    def __init__(self):
        self.graph = nx.Graph()
        self.vectorizer = TfidfVectorizer(stop_words='english')
    
    def add_claim(self, claim: Dict[str, Any]):
        """Add a claim to the graph"""
        claim_id = str(claim['id'])
        
        # Add claim node
        self.graph.add_node(
            claim_id,
            type='claim',
            text=claim['claim_text'],
            subject=claim.get('subject', ''),
            predicate=claim.get('predicate', ''),
            object=claim.get('object', ''),
            confidence=claim.get('confidence', 0.0),
            status=claim.get('status', 'Unknown'),
            created_at=claim.get('created_at', datetime.now().isoformat())
        )
        
        # Add edges to similar claims
        self._add_similarity_edges(claim_id, claim)
    
    def _add_similarity_edges(self, claim_id: str, claim: Dict[str, Any]):
        """Add edges between similar claims based on content similarity"""
        if len(self.graph.nodes) < 2:
            return
        
        # Get text representation of the claim
        claim_text = f"{claim.get('subject', '')} {claim.get('predicate', '')} {claim.get('object', '')}"
        
        # Get all existing claim texts
        existing_claims = {
            node: data['text']
            for node, data in self.graph.nodes(data=True)
            if node != claim_id
        }
        
        if not existing_claims:
            return
        
        # Calculate similarity scores
        texts = list(existing_claims.values()) + [claim_text]
        tfidf_matrix = self.vectorizer.fit_transform(texts)
        similarity_scores = cosine_similarity(tfidf_matrix[-1:], tfidf_matrix[:-1])[0]
        
        # Add edges for similar claims
        for node, score in zip(existing_claims.keys(), similarity_scores):
            if score > 0.3:  # Similarity threshold
                self.graph.add_edge(
                    claim_id,
                    node,
                    weight=score,
                    type='similarity'
                )
    
    def get_connected_claims(self, claim_id: str, max_depth: int = 2) -> List[Dict[str, Any]]:
        """Get claims connected to a specific claim within max_depth"""
        if claim_id not in self.graph:
            return []
        
        connected_nodes = set()
        current_nodes = {claim_id}
        
        for _ in range(max_depth):
            next_nodes = set()
            for node in current_nodes:
                neighbors = set(self.graph.neighbors(node))
                next_nodes.update(neighbors)
            connected_nodes.update(next_nodes)
            current_nodes = next_nodes
        
        return [
            {
                'id': node,
                **self.graph.nodes[node]
            }
            for node in connected_nodes
        ]
    
    def get_community_claims(self) -> List[List[str]]:
        """Get communities of related claims using Louvain method"""
        if len(self.graph.nodes) < 2:
            return []
        
        try:
            import community
            partition = community.best_partition(self.graph)
            communities = {}
            for node, community_id in partition.items():
                if community_id not in communities:
                    communities[community_id] = []
                communities[community_id].append(node)
            return list(communities.values())
        except ImportError:
            # Fallback to connected components if community detection is not available
            return list(nx.connected_components(self.graph))
    
    def to_json(self) -> str:
        """Convert graph to JSON format for visualization"""
        graph_data = {
            'nodes': [
                {
                    'id': node,
                    **data
                }
                for node, data in self.graph.nodes(data=True)
            ],
            'edges': [
                {
                    'source': source,
                    'target': target,
                    **data
                }
                for source, target, data in self.graph.edges(data=True)
            ]
        }
        return json.dumps(graph_data)
    
    def from_json(self, json_data: str):
        """Load graph from JSON format"""
        data = json.loads(json_data)
        self.graph.clear()
        
        # Add nodes
        for node in data['nodes']:
            node_id = node.pop('id')
            self.graph.add_node(node_id, **node)
        
        # Add edges
        for edge in data['edges']:
            source = edge.pop('source')
            target = edge.pop('target')
            self.graph.add_edge(source, target, **edge)
    
    def get_central_claims(self, top_n: int = 5) -> List[Dict[str, Any]]:
        """Get the most central claims in the graph"""
        if len(self.graph.nodes) < 2:
            return []
        
        # Calculate centrality scores
        centrality = nx.betweenness_centrality(self.graph)
        
        # Get top N central claims
        central_nodes = sorted(
            centrality.items(),
            key=lambda x: x[1],
            reverse=True
        )[:top_n]
        
        return [
            {
                'id': node,
                'centrality': score,
                **self.graph.nodes[node]
            }
            for node, score in central_nodes
        ] 
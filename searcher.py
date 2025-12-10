"""
PyLucene Music Search Engine - Searcher
Search indexed music with AND/OR queries, filters, and weighting
"""
import lucene
import re
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.index import DirectoryReader
from org.apache.lucene.queryparser.classic import QueryParser, MultiFieldQueryParser
from org.apache.lucene.search import IndexSearcher, BooleanQuery, BooleanClause
from org.apache.lucene.document import IntPoint
from org.apache.lucene.store import FSDirectory
from java.nio.file import Paths
from java.util import HashMap
from java.lang import Float

class MusicSearcher:
    def __init__(self, index_dir):
        # Don't initialize VM here - let caller handle it
        if not lucene.getVMEnv():
            lucene.initVM()
        store = FSDirectory.open(Paths.get(index_dir))
        self.reader = DirectoryReader.open(store)
        self.searcher = IndexSearcher(self.reader)
        self.analyzer = StandardAnalyzer()
    
    def search(self, query_text, field="name", max_results=10):
        """Simple single-field search"""
        parser = QueryParser(field, self.analyzer)
        # Call instance method explicitly
        query = QueryParser.parse(parser, query_text)
        
        hits = self.searcher.search(query, max_results)
        
        results = []
        for hit in hits.scoreDocs:
            doc = self.searcher.storedFields().document(hit.doc)
            results.append({
                'score': hit.score,
                'name': doc.get('name'),
                'composer': doc.get('composer'),
                'key': doc.get('key'),
                'year': doc.get('year'),
                'level': doc.get('level'),
                'period': doc.get('period'),
                'url': doc.get('url'),
                'wiki_title': doc.get('wiki_title'),
                'wiki_composer': doc.get('wiki_composer'),
                'info_catalogue': doc.get('info_catalogue'),
                'info_opus': doc.get('info_opus'),
                'info_genre': doc.get('info_genre'),
                'info_composed': doc.get('info_composed')
            })
        
        return results
    
    def parse_query(self, query_text):
        """Parse query to extract filters and main search text"""
        filters = {
            'year_range': None,
            'difficulty': None
        }
        
        # Extract year range: year:1850-1875 or year:1850
        year_match = re.search(r'year:(\d{4})(?:-(\d{4}))?', query_text, re.IGNORECASE)
        if year_match:
            start_year = int(year_match.group(1))
            end_year = int(year_match.group(2)) if year_match.group(2) else start_year
            filters['year_range'] = (start_year, end_year)
            # Remove year filter from query text
            query_text = re.sub(r'year:\d{4}(?:-\d{4})?\s*', '', query_text, flags=re.IGNORECASE)
        
        # Extract difficulty filter: difficulty:easy, difficulty:hard, etc.
        difficulty_match = re.search(r'difficulty:(easy|intermediate|medium|hard)', query_text, re.IGNORECASE)
        if difficulty_match:
            difficulty_value = difficulty_match.group(1).lower()
            difficulty_keywords = {
                'easy': (0, 2),
                'intermediate': (3, 5),
                'medium': (3, 5),
                'hard': (6, 10)
            }
            if difficulty_value in difficulty_keywords:
                filters['difficulty'] = difficulty_keywords[difficulty_value]
            # Remove difficulty filter from query text
            query_text = re.sub(r'difficulty:(easy|intermediate|medium|hard)\s*', '', query_text, flags=re.IGNORECASE)
        
        return query_text.strip(), filters
    
    def multi_field_search(self, query_text, max_results=10):
        """Search across name, composer, description, and Wikipedia fields with boosting"""
        # Parse query for filters
        clean_query, filters = self.parse_query(query_text)
        
        # Build the main text query
        fields = ["name", "composer", "description", "summary", "wiki_title", "wiki_paragraph", "info_genre", "info_form", "info_movements"]
        
        # Create boost map
        boosts = {
            "name": 3.0,
            "composer": 2.5,
            "wiki_title": 2.0,
            "wiki_paragraph": 1.5,
            "info_genre": 1.2,
            "description": 1.0,
            "summary": 1.0,
            "info_form": 0.8,
            "info_movements": 0.8
        }
        
        # Convert Python dict to Java HashMap for boosts
        boost_map = HashMap()
        for field, boost in boosts.items():
            boost_map.put(field, Float(boost))
        
        # Create the boolean query builder
        builder = BooleanQuery.Builder()
        
        # Add the main text query if there's any text left
        if clean_query:
            parser = MultiFieldQueryParser(fields, self.analyzer, boost_map)
            text_query = MultiFieldQueryParser.parse(parser, clean_query)
            builder.add(text_query, BooleanClause.Occur.MUST)
        
        # Add year range filter
        if filters['year_range']:
            start_year, end_year = filters['year_range']
            year_query = IntPoint.newRangeQuery('year_range', start_year, end_year)
            builder.add(year_query, BooleanClause.Occur.MUST)
        
        # Add difficulty filter (level range)
        if filters['difficulty']:
            min_level, max_level = filters['difficulty']
            level_query = IntPoint.newRangeQuery('level_range', min_level, max_level)
            builder.add(level_query, BooleanClause.Occur.MUST)
        
        final_query = builder.build()
        
        # If no query components, return empty
        if final_query.clauses().size() == 0:
            return []
        
        hits = self.searcher.search(final_query, max_results)
        
        results = []
        for hit in hits.scoreDocs:
            doc = self.searcher.storedFields().document(hit.doc)
            results.append({
                'score': hit.score,
                'name': doc.get('name'),
                'composer': doc.get('composer'),
                'key': doc.get('key'),
                'year': doc.get('year'),
                'level': doc.get('level'),
                'period': doc.get('period'),
                'url': doc.get('url'),
                'wiki_title': doc.get('wiki_title'),
                'info_composer': doc.get('info_composer'),
                'info_key': doc.get('info_key'),
                'info_catalogue': doc.get('info_catalogue'),
                'info_opus': doc.get('info_opus'),
                'info_form': doc.get('info_form'),
                'info_genre': doc.get('info_genre'),
                'info_composed': doc.get('info_composed')
            })
        
        return results
    
    def close(self):
        self.reader.close()
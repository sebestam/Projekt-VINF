"""PyLucene Music Search Engine - Indexer
Indexes music_enriched.csv with Wikipedia-enhanced fields
"""
import lucene
import csv
from pathlib import Path
from org.apache.lucene.analysis.standard import StandardAnalyzer
from org.apache.lucene.document import Document, Field, TextField, StringField, StoredField, IntPoint, NumericDocValuesField
from org.apache.lucene.index import IndexWriter, IndexWriterConfig
from org.apache.lucene.store import FSDirectory
from java.nio.file import Paths

def create_index(csv_path, index_dir):
    """Create Lucene index from music CSV"""
    # Initialize VM if not already running
    if not lucene.getVMEnv():
        lucene.initVM()
    
    # Create index directory
    store = FSDirectory.open(Paths.get(index_dir))
    analyzer = StandardAnalyzer()
    config = IndexWriterConfig(analyzer)
    config.setOpenMode(IndexWriterConfig.OpenMode.CREATE)
    writer = IndexWriter(store, config)
    
    print(f"Indexing {csv_path}...")
    count = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            doc = Document()
            
            # TextField = tokenized, full-text searchable
            # Name (searchable + stored)
            if row.get('name') and row['name'].strip():
                doc.add(TextField('name', row['name'], Field.Store.YES))
            
            # Composer (searchable + stored)
            if row.get('composer') and row['composer'].strip():
                doc.add(TextField('composer', row['composer'], Field.Store.YES))
            
            # Description (searchable, not stored - saves space)
            if row.get('description'):
                doc.add(TextField('description', row['description'], Field.Store.NO))
            
            # Summary (searchable, not stored)
            if row.get('summary'):
                doc.add(TextField('summary', row['summary'], Field.Store.NO))
            
            # Wikipedia paragraph (searchable, not stored)
            if row.get('wiki_paragraph'):
                doc.add(TextField('wiki_paragraph', row['wiki_paragraph'], Field.Store.NO))
            
            # Genre from Wikipedia infobox (searchable + stored)
            if row.get('info_genre'):
                doc.add(TextField('info_genre', row['info_genre'], Field.Store.YES))
            
            # Form from Wikipedia infobox (searchable + stored)
            if row.get('info_form'):
                doc.add(TextField('info_form', row['info_form'], Field.Store.YES))
            
            # Movements from Wikipedia infobox (searchable, not stored)
            if row.get('info_movements'):
                doc.add(TextField('info_movements', row['info_movements'], Field.Store.NO))
            
            # StringField = exact match only, not tokenized
            # Key (exact match + stored)
            if row.get('key'):
                doc.add(StringField('key', row['key'], Field.Store.YES))
            
            # Year - indexed for range queries + stored as string
            if row.get('year') and row['year'].strip():
                try:
                    year_int = int(row['year'])
                    # IntPoint for range queries
                    doc.add(IntPoint('year_range', year_int))
                    # NumericDocValuesField for sorting
                    doc.add(NumericDocValuesField('year_sort', year_int))
                    # StringField for display
                    doc.add(StringField('year', row['year'], Field.Store.YES))
                except ValueError:
                    # If year is not a valid integer, just store as string
                    doc.add(StringField('year', row['year'], Field.Store.YES))
            
            # Level - indexed for range queries (difficulty) + stored as string
            if row.get('level') and row['level'].strip():
                try:
                    level_int = int(row['level'])
                    # IntPoint for range queries (difficulty filtering)
                    doc.add(IntPoint('level_range', level_int))
                    # NumericDocValuesField for sorting
                    doc.add(NumericDocValuesField('level_sort', level_int))
                    # StringField for display
                    doc.add(StringField('level', row['level'], Field.Store.YES))
                except ValueError:
                    # If level is not a valid integer, just store as string
                    doc.add(StringField('level', row['level'], Field.Store.YES))
            
            # Period (exact match + stored)
            if row.get('period'):
                doc.add(StringField('period', row['period'], Field.Store.YES))
            
            # Catalogue from Wikipedia (exact match + stored)
            if row.get('info_catalogue'):
                doc.add(StringField('info_catalogue', row['info_catalogue'], Field.Store.YES))
            
            # Opus from Wikipedia (exact match + stored)
            if row.get('info_opus'):
                doc.add(StringField('info_opus', row['info_opus'], Field.Store.YES))
            
            # Composed year from Wikipedia (exact match + stored)
            if row.get('info_composed'):
                doc.add(StringField('info_composed', row['info_composed'], Field.Store.YES))
            
            # StoredField = only stored, not searchable
            # URL (stored only)
            if row.get('url'):
                doc.add(StoredField('url', row['url']))
            
            # Wikipedia title (searchable + stored)
            if row.get('wiki_title'):
                doc.add(TextField('wiki_title', row['wiki_title'], Field.Store.YES))
            
            # Wikipedia composer (searchable + stored)
            if row.get('wiki_composer'):
                doc.add(TextField('wiki_composer', row['wiki_composer'], Field.Store.YES))
            
            # Related downloads - searchable
            if row.get('related_downloads'):
                doc.add(TextField('related', row['related_downloads'], Field.Store.NO))
            
            writer.addDocument(doc)
            count += 1
            
            if count % 100 == 0:
                print(f"  Indexed {count} documents...")
    
    writer.commit()
    writer.close()
    
    print(f"✅ Indexed {count} music pieces to {index_dir}")

if __name__ == "__main__":
    csv_path = "/data/music_enriched.csv"
    index_dir = "/data/music_index"
    
    create_index(csv_path, index_dir)
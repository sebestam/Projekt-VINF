# PyLucene Music Search Engine - Code Documentation

## Overview
A Docker-based search engine for classical piano music using Apache Lucene through PyLucene. Indexes 3,919 music pieces from pianostreet.com crawl data with weighted fields for intelligent ranking.

---

## Architecture

```
main.py           → Menu interface (index/search/exit)
  ├─ indexer.py   → Creates Lucene index from CSV
  ├─ search_cli.py → Interactive search interface
  └─ searcher.py  → Core search logic with PyLucene
```

---

## Files

### `main.py` - Entry Point & Menu System

**Purpose**: Main menu controller that runs in Docker container

**Key Functions**:
- `show_menu()` - Displays options: 1) Index, 2) Search, 3) Exit
- `run_indexer()` - Validates CSV exists, calls indexer, waits for user
- `run_search()` - Validates index exists, launches search CLI
- `main()` - Initializes JVM once, loops menu until exit

**Flow**:
1. Initialize PyLucene JVM (`lucene.initVM()`)
2. Show menu in infinite loop
3. Route to indexer or searcher based on choice
4. Handle KeyboardInterrupt gracefully (prompt for option 3)

**Docker Integration**:
- Expects `/data/music_results.csv` (mounted from host)
- Expects `/data/music_index` (persistent volume for index)

---

### `indexer.py` - Index Creation

**Purpose**: Parse CSV and build searchable Lucene index

**Main Function**: `create_index(csv_path, index_dir)`

**Process**:
1. Initialize JVM if not already running (`lucene.getVMEnv()` check)
2. Open FSDirectory at `/data/music_index`
3. Create IndexWriter with StandardAnalyzer
4. Read CSV with Python's `csv.DictReader`
5. For each music piece:
   - Create Lucene Document
   - Add fields with different storage/indexing strategies
6. Commit and close writer

**Field Strategy**:
```python
# SEARCHABLE + STORED (for display)
TextField('name', ...)          # Music piece title
TextField('composer', ...)      # Composer name

# SEARCHABLE ONLY (boost relevance, not displayed)
TextField('description', ...)   # Description text
TextField('summary', ...)       # Summary text
TextField('related', ...)       # Related downloads

# EXACT MATCH + STORED (filters)
StringField('key', ...)         # Musical key (e.g., "C Major")
StringField('year', ...)        # Composition year
StringField('level', ...)       # Difficulty level
StringField('period', ...)      # Musical period

# STORED ONLY (display URL)
StoredField('url', ...)         # Link to sheet music
```

**Performance**:
- Processes ~3,919 documents
- Progress updates every 100 documents
- Takes ~10-15 seconds on average

---

### `searcher.py` - Search Backend

**Purpose**: Core search functionality using PyLucene API

**Class**: `MusicSearcher`

**Initialization**:
```python
def __init__(self, index_dir):
    # Check if JVM already running (don't reinitialize)
    if not lucene.getVMEnv():
        lucene.initVM()
    
    # Open index directory
    store = FSDirectory.open(Paths.get(index_dir))
    self.reader = DirectoryReader.open(store)
    self.searcher = IndexSearcher(self.reader)
    self.analyzer = StandardAnalyzer()
```

**Key Methods**:

#### `search(query_text, field="name", max_results=10)`
Single-field search (default: search in "name" only)

```python
parser = QueryParser(field, self.analyzer)
query = QueryParser.parse(parser, query_text)
hits = self.searcher.search(query, max_results)
```

#### `multi_field_search(query_text, max_results=10)`
Multi-field search across name, composer, description, summary

```python
fields = ["name", "composer", "description", "summary"]
parser = MultiFieldQueryParser(fields, self.analyzer)
query = MultiFieldQueryParser.parse(parser, query_text)
```

**Important PyLucene Quirks**:
- Must call `QueryParser.parse(parser, text)` NOT `parser.parse(text)`
  - Descriptor issue with JCC Python-Java bridge
- Must use `searcher.storedFields().document(docId)` in Lucene 10.x
  - Old API `searcher.doc(docId)` removed
- HashMap for boosts currently disabled (simple equal-weight search)

**Return Format**:
```python
{
    'score': 9.414,                              # Relevance score
    'name': 'Sonata 20 in G Major, Op. 49 No. 2',
    'composer': 'Ludwig van Beethoven',
    'key': 'G Major',
    'year': '1797',
    'level': '5',
    'period': 'Classical',
    'url': 'https://...'
}
```

---

### `search_cli.py` - Interactive CLI

**Purpose**: User-facing search prompt with command loop

**Main Function**: `main()`

**Flow**:
1. Initialize JVM if needed
2. Print commands help
3. Create MusicSearcher instance
4. Enter input loop:
   ```
   > beethoven sonata
   > back           (return to menu)
   > quit/exit      (exit program with sys.exit(0))
   ```

**Search Results Display**:
- Shows top 5 results by default
- Displays: name, composer, key, year, level, score
- If more results: shows "... and X more results"

**Error Handling**:
- `EOFError` - graceful exit on Ctrl+D
- `KeyboardInterrupt` - remind user to type 'quit'
- Generic exceptions - print error and continue

**Exit Strategy**:
- `back` → breaks loop, returns to main.py menu
- `quit/exit` → calls `sys.exit(0)`, terminates entire program

---

## Docker Setup

### `Dockerfile.extended`
```dockerfile
FROM coady/pylucene:latest
RUN pip install pandas
COPY *.py /app/
CMD ["python", "main.py"]
```

### `docker-compose.yml`
```yaml
services:
  music-search:
    volumes:
      - ../music_results.csv:/data/music_results.csv:ro
      - ./index_data:/data/music_index
    stdin_open: true
    tty: true
```

**Usage**:
```bash
cd pylucene
docker-compose run --rm music-search
```

The `--rm` flag auto-removes container on exit (no buildup).

---

## Data Flow

### Indexing (Option 1):
```
CSV File (3,919 rows)
  → csv.DictReader()
  → Lucene Document (with fields)
  → IndexWriter.addDocument()
  → Commit to /data/music_index/
```

### Searching (Option 2):
```
User Query: "beethoven sonata"
  → StandardAnalyzer (tokenize: [beethoven, sonata])
  → MultiFieldQueryParser (search: name, composer, description, summary)
  → IndexSearcher.search()
  → Score & rank results
  → Display top 5
```

---

## PyLucene Specifics

### JVM Management
- Must call `lucene.initVM()` once per process
- Use `lucene.getVMEnv()` to check if already running
- Cannot reinitialize (raises `ValueError`)

### StandardAnalyzer
- Lowercases text
- Removes stop words (the, a, an, etc.)
- Tokenizes on whitespace/punctuation
- Example: "Beethoven's Sonata" → [beethoven, sonata]

### Field Types
| Field Type | Indexed | Stored | Tokenized | Use Case |
|------------|---------|--------|-----------|----------|
| TextField | ✓ | Optional | ✓ | Full-text search |
| StringField | ✓ | ✓ | ✗ | Exact match filters |
| StoredField | ✗ | ✓ | ✗ | Display only |

### Scoring
- TF-IDF with cosine similarity (Lucene default)
- Higher score = more relevant
- Matches in multiple fields boost score
- Term frequency matters (repeated words increase relevance)

---

## Known Limitations

1. **No Field Boosting Yet**
   - Currently equal weight across fields
   - TODO: Implement HashMap boosts (name^3, composer^2)

2. **No Advanced Queries**
   - No AND/OR operators yet
   - No year range filtering
   - No fuzzy matching

3. **Top 5 Results Only**
   - More results available but not shown
   - Could add pagination

4. **No Relevance Tuning**
   - Default Lucene scoring
   - Could customize with BM25 or custom similarity

---

## Future Enhancements (from TODO)

- [ ] Boolean queries (AND/OR)
- [ ] Year range filtering
- [ ] Field boosting (name > composer > description)
- [ ] Fuzzy search (handle typos)
- [ ] Recommendations (based on related_downloads)
- [ ] Phrase queries ("moonlight sonata" as phrase)
- [ ] Faceted search (filter by level, period, key)

---

## Troubleshooting

**Issue**: "cannot import name 'index_music'"
- **Cause**: Function renamed to `create_index`
- **Fix**: Update imports in main.py

**Issue**: "JVM is already running"
- **Cause**: Multiple `lucene.initVM()` calls
- **Fix**: Check with `lucene.getVMEnv()` first

**Issue**: "'IndexSearcher' object has no attribute 'doc'"
- **Cause**: Lucene 10.x API change
- **Fix**: Use `searcher.storedFields().document(docId)`

**Issue**: "descriptor 'parse' doesn't apply to 'str'"
- **Cause**: PyLucene JCC descriptor issue
- **Fix**: Call `QueryParser.parse(parser, text)` not `parser.parse(text)`

**Issue**: Container keeps running after exit
- **Cause**: Using `docker-compose up` instead of `run`
- **Fix**: Use `docker-compose run --rm music-search`

---

## Testing Queries

Good test queries to verify search works:
- `beethoven` - Should return Beethoven sonatas
- `mozart sonata` - Multi-word search
- `major` - Should match musical keys
- `chopin nocturne` - Composer + piece type
- `1800` - Year-based search (searches all fields)

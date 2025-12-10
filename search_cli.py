"""
Interactive CLI for PyLucene Music Search Engine
Persistent search interface
"""
import lucene
from searcher import MusicSearcher

def main():
    # Initialize VM if not already running
    if not lucene.getVMEnv():
        lucene.initVM()
    
    print("=" * 60)
    print("PyLucene Music Search Engine")
    print("=" * 60)
    print("\nCommands:")
    print("  <query>         - Search for music")
    print("  back            - Return to main menu")
    print("  quit/exit       - Exit program")
    print("\nSearch examples:")
    print("  beethoven                         - Search by composer")
    print("  sonata                            - Search by form/name")
    print("  year:1850-1875                    - Filter by year range")
    print("  beethoven year:1800-1810          - Combine text + year filter")
    print("  difficulty:easy                   - Find easy pieces (level < 3)")
    print("  difficulty:intermediate           - Find intermediate (level 3-5)")
    print("  difficulty:hard                   - Find hard pieces (level > 6)")
    print("  chopin difficulty:hard            - Combine composer + difficulty")
    print("  sonata year:1850-1900 difficulty:hard - All filters combined")
    print("=" * 60)
    
    searcher = MusicSearcher("/data/music_index")
    
    try:
        while True:
            try:
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("Exiting...")
                    import sys
                    sys.exit(0)
                
                if user_input.lower() == 'back':
                    print("Returning to menu...")
                    break
                
                print(f"\nSearching for: '{user_input}'")
                print("-" * 60)
                
                results = searcher.multi_field_search(user_input, max_results=20)
                
                if not results:
                    print("No results found.")
                else:
                    for i, result in enumerate(results, 1):
                        # Check if this is from original music data (has name) or only Wikipedia
                        name = result.get('name')
                        has_music_data = name is not None and name.strip() != '' and name != 'None'
                        has_wiki_data = result.get('wiki_title') and result['wiki_title'].strip()
                        
                        if has_music_data:
                            # Original music data exists - show music info
                            print(f"\n{i}. {result['name']}")
                            print(f"   Composer: {result['composer']}")
                            
                            if has_wiki_data:
                                # Also has Wikipedia enrichment
                                print(f"   Wikipedia: {result['wiki_title']}")
                                if result.get('info_catalogue') and result['info_catalogue'].strip():
                                    print(f"   Catalogue: {result['info_catalogue']}")
                                if result.get('info_opus') and result['info_opus'].strip():
                                    print(f"   Opus: {result['info_opus']}")
                                if result.get('info_genre') and result['info_genre'].strip():
                                    print(f"   Genre: {result['info_genre']}")
                                if result.get('info_composed') and result['info_composed'].strip():
                                    print(f"   Composed: {result['info_composed']}")
                            
                            print(f"   Key: {result.get('key', 'N/A')}, Year: {result.get('year', 'N/A')}, Level: {result.get('level', 'N/A')}")
                        
                        else:
                            # Only Wikipedia data (unmatched wiki entry)
                            wiki_title = result.get('wiki_title', 'Unknown')
                            print(f"\n{i}. {wiki_title}")
                            composer = result.get('info_composer') or result.get('wiki_composer')
                            if composer and composer.strip():
                                print(f"   Composer: {composer}")
                            if result.get('info_key') and result['info_key'].strip():
                                print(f"   Key: {result['info_key']}")
                            if result.get('info_catalogue') and result['info_catalogue'].strip():
                                print(f"   Catalogue: {result['info_catalogue']}")
                            if result.get('info_opus') and result['info_opus'].strip():
                                print(f"   Opus: {result['info_opus']}")
                            if result.get('info_form') and result['info_form'].strip():
                                print(f"   Form: {result['info_form']}")
                            if result.get('info_genre') and result['info_genre'].strip():
                                print(f"   Genre: {result['info_genre']}")
                            if result.get('info_composed') and result['info_composed'].strip():
                                print(f"   Composed: {result['info_composed']}")
                            print(f"   [Wikipedia only]")
                        
                        print(f"   Score: {result['score']:.3f}")
                        if i >= 10:  # Show top 10 by default
                            if len(results) > 10:
                                print(f"\n... and {len(results) - 10} more results")
                            break
                
            except EOFError:
                print("\nGoodbye!")
                break
            except KeyboardInterrupt:
                print("\nUse 'quit' or 'exit' to close")
            except Exception as e:
                print(f"Error: {e}")
                import traceback
                traceback.print_exc()
    
    finally:
        searcher.close()

if __name__ == "__main__":
    main()
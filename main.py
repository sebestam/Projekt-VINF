"""
PyLucene Music Search - Main Menu
Single container for indexing and searching
"""
import lucene
import os
import sys

def show_menu():
    print("\n" + "=" * 60)
    print("PyLucene Music Search Engine")
    print("=" * 60)
    print("\n1. Index music data (run once)")
    print("2. Search music")
    print("3. Metrics (evaluate searcher)")
    print("4. Exit")
    print("=" * 60)

def run_indexer():
    print("\n" + "=" * 60)
    print("INDEXING MUSIC DATA")
    print("=" * 60)
    
    # Check if CSV exists
    csv_path = "/data/music_enriched.csv"
    if not os.path.exists(csv_path):
        print(f"ERROR: {csv_path} not found!")
        print("Make sure to mount music_enriched.csv to /data/")
        return
    
    from indexer import create_index
    index_dir = "/data/music_index"
    create_index(csv_path, index_dir)
    
    print("\nIndexing complete! Press Enter to continue...")
    input()

def run_search():
    print("\n" + "=" * 60)
    print("INTERACTIVE SEARCH")
    print("=" * 60)
    
    # Check if index exists
    index_path = "/data/music_index"
    if not os.path.exists(index_path) or not os.listdir(index_path):
        print(f"ERROR: No index found at {index_path}")
        print("Please run 'Index music data' first (option 1)")
        print("\nPress Enter to continue...")
        input()
        return
    
    from search_cli import main as search_main
    print("\nType your search queries. Use 'back' to return to menu, 'quit' to exit.\n")
    search_main()

def run_metrics():
    metrics_path = os.path.join(os.path.dirname(__file__), "test_metrics.py")
    # Use the same Python interpreter
    exit_code = os.system(f"{sys.executable} {metrics_path}")
    if exit_code != 0:
        print("Error running metrics evaluation.")

def main():
    # Initialize JVM once
    lucene.initVM()
    
    while True:
        show_menu()
        
        try:
            choice = input("\nSelect option (1-4): ").strip()
            
            if choice == "1":
                run_indexer()
            elif choice == "2":
                run_search()
            elif choice == "3":
                run_metrics()
            elif choice == "4":
                print("\nGoodbye!")
                break
            else:
                print("\nInvalid choice. Please select 1, 2, 3, or 4.")
                
        except KeyboardInterrupt:
            print("\n\nUse option 4 to exit properly.")
        except Exception as e:
            print(f"\nError: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()

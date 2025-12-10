import json
from searcher import MusicSearcher
from sklearn.metrics import precision_score, recall_score, f1_score

def evaluate_searcher(index_dir, queries_file):
    """Evaluate the searcher using precision, recall, and F1 metrics."""
    index_dir = "/data/music_index"  # Update with the correct path
    queries_file = "/data/queries.json"  # Update with the correct path

    # Load queries and expected results
    with open(queries_file, 'r') as f:
        data = json.load(f)

    searcher = MusicSearcher(index_dir)

    queries = data['queries']

    try:
        all_precisions = []
        all_recalls = []
        all_f1s = []

        for query_data in queries:
            query = query_data['query']
            expected_results = query_data['expected_results']

            # Perform search
            results = searcher.multi_field_search(query, max_results=10)
            retrieved_results = [result['name'] for result in results if result.get('name')]

            # Compute metrics
            y_true = [1 if result in expected_results else 0 for result in retrieved_results]
            y_pred = [1] * len(retrieved_results)

            precision = precision_score(y_true, y_pred, zero_division=0)
            recall = recall_score(y_true, y_pred, zero_division=0)
            f1 = f1_score(y_true, y_pred, zero_division=0)

            all_precisions.append(precision)
            all_recalls.append(recall)
            all_f1s.append(f1)

            print(f"Query: {query}")
            print(f"Precision: {precision:.2f}, Recall: {recall:.2f}, F1: {f1:.2f}\n")

        # Compute average metrics
        avg_precision = sum(all_precisions) / len(all_precisions)
        avg_recall = sum(all_recalls) / len(all_recalls)
        avg_f1 = sum(all_f1s) / len(all_f1s)

        print("Overall Metrics:")
        print(f"Average Precision: {avg_precision:.2f}")
        print(f"Average Recall: {avg_recall:.2f}")
        print(f"Average F1: {avg_f1:.2f}")

    finally:
        searcher.close()

if __name__ == "__main__":
    evaluate_searcher("/data/music_index", "/data/queries.json")



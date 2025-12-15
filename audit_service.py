import random
# Use a relative import assuming audit_categories.py is in the same package
from .audit_categories import AUDIT_CATEGORIES 

# Define the possible audit outcomes
AUDIT_STATUSES = ['Excellent', 'Good', 'Fair', 'Poor', 'N/A']

class AuditService:
    """
    Handles the core logic for running a website audit, simulating metric checks,
    and calculating category and overall scores based on the full list of categories.
    """

    @staticmethod
    def _simulate_metric_check(metric_name: str) -> str:
        """
        A placeholder for actual audit logic (e.g., calling external tools). 
        Returns a random status for demonstration.
        """
        # A simple check to ensure 'N/A' is less common for simulation
        weights = [4, 4, 3, 2, 1] 
        return random.choices(AUDIT_STATUSES, weights=weights, k=1)[0]


    @staticmethod
    def run_audit(url: str):
        """
        Executes a simulated audit against the given URL and structures the results.
        """
        metrics_status_map = {}
        categories_result = {}

        # 1. Run checks for all categories and metrics
        for category, info in AUDIT_CATEGORIES.items():
            
            # Initialize category structure for the final result
            categories_result[category] = {
                "description": info["desc"], 
                "items": []
            }
            
            for metric in info["metrics"]:
                # Simulate the check for the metric
                status = AuditService._simulate_metric_check(metric)
                
                # Store metric status globally (flat map)
                metrics_status_map[metric] = status
                
                # Store structured metric result within its category
                categories_result[category]["items"].append({
                    "name": metric,
                    "status": status,
                    # Placeholder for real-world suggestion logic
                    "suggestion": f"Check documentation for best practice on '{metric}'." 
                })

        # 2. Calculate scores using the complete map of results
        scores = AuditService.calculate_score(metrics_status_map)

        # 3. Return the comprehensive result
        return {
            "url": url,
            "metrics_map": metrics_status_map,  # Flat map of all metric statuses
            "categories": categories_result,    # Structured result organized by category
            "scores": scores                    # Calculated category and overall scores
        }

    @staticmethod
    def calculate_score(metrics_status_map: dict) -> dict:
        """
        Calculates category scores based on metric statuses across all defined categories.
        """
        
        def score_category(category_metrics_statuses: list) -> float:
            """Calculates the score for a single category."""
            
            # Filter out 'N/A' metrics, as they should not count against the total
            valid_metrics = [v for v in category_metrics_statuses if v != 'N/A']
            total_count = len(valid_metrics)
            
            if total_count == 0:
                return 0.00

            # Scoring weights: Excellent=1, Good=0.5, Fair/Poor=0
            excellent = sum(1 for v in valid_metrics if v == 'Excellent')
            good = sum(0.5 for v in valid_metrics if v == 'Good')
            
            raw_score = (excellent + good) / total_count
            return round(raw_score * 100, 2)

        all_scores = {}
        category_scores_list = []
        
        # Iterate over ALL categories in AUDIT_CATEGORIES
        for category, info in AUDIT_CATEGORIES.items():
            
            # 1. Get the list of statuses for the metrics in this specific category
            category_metrics_statuses = [
                metrics_status_map.get(metric, 'N/A')
                for metric in info["metrics"]
            ]
            
            # 2. Calculate the score
            score = score_category(category_metrics_statuses)
            
            # 3. Store the result with a standardized key (e.g., performance_score)
            score_key = f"{category.lower().replace(' ', '_')}_score"
            all_scores[score_key] = score
            category_scores_list.append(score)

        # Calculate Overall Score (Average of all valid category scores)
        if category_scores_list:
            all_scores["overall_score"] = round(sum(category_scores_list) / len(category_scores_list), 2)
        else:
            all_scores["overall_score"] = 0.00

        # The 'organize_metrics' method is now redundant and its logic is integrated 
        # into 'run_audit', so it has been removed.
        return all_scores

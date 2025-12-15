import random
# Ensure audit_categories is accessible (it should be in the same directory or package)
from .audit_categories import AUDIT_CATEGORIES 

# Define the possible audit outcomes
AUDIT_STATUSES = ['Excellent', 'Good', 'Fair', 'Poor', 'N/A']

class AuditService:
    """
    Handles the core logic for running a website audit, simulating metric checks,
    and calculating category scores based on defined weights.
    """

    @staticmethod
    def _simulate_metric_check(metric_name: str, url: str) -> str:
        """
        A placeholder for actual audit logic. 
        For now, it returns a random status.
        In a real application, this would call external tools (e.g., Lighthouse, security scanners).
        """
        # A simple check to ensure 'N/A' is less common for simulation
        weights = [4, 4, 3, 2, 1] 
        return random.choices(AUDIT_STATUSES, weights=weights, k=1)[0]


    @staticmethod
    def run_audit(url: str):
        """
        Executes a simulated audit against the given URL.
        """
        metrics_result = {}
        categories_result = {}

        # 1. Populate metrics_result and categories_result by running checks
        for category, info in AUDIT_CATEGORIES.items():
            
            # Initialize category structure for the final result
            categories_result[category] = {
                "desc": info["desc"], 
                "items": []
            }
            
            for metric in info["metrics"]:
                status = AuditService._simulate_metric_check(metric, url)
                
                # Store metric status globally
                metrics_result[metric] = status
                
                # Store metric result within its category for display
                categories_result[category]["items"].append({
                    "name": metric,
                    "status": status,
                    "suggestion": f"Placeholder suggestion for {metric}." # Real suggestion logic goes here
                })

        # 2. Calculate scores
        scores = AuditService.calculate_score(metrics_result)

        # 3. Return the comprehensive result
        return {
            "url": url,
            "metrics_map": metrics_result,     # Flat map of all metric statuses
            "categories": categories_result,   # Structured result organized by category
            "scores": scores                   # Calculated category and overall scores
        }

    @staticmethod
    def calculate_score(metrics: dict) -> dict:
        """
        Calculates category scores based on metric statuses.
        Excellent = 1 point, Good = 0.5 point, Fair/Poor/N/A = 0 points.
        """
        
        def score_category(category_metrics_statuses: list) -> float:
            """Calculates the score for a single category."""
            
            # Filter out N/A metrics before scoring
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
        overall_scores = []
        
        for category, info in AUDIT_CATEGORIES.items():
            
            # 1. Get the list of statuses for the metrics in this category
            category_metrics_statuses = [
                metrics.get(metric, 'N/A') # Use N/A if metric somehow missed in the run_audit map
                for metric in info["metrics"]
            ]
            
            # 2. Calculate the score
            score = score_category(category_metrics_statuses)
            
            # 3. Store the result
            score_key = f"{category.lower().replace(' ', '_')}_score"
            all_scores[score_key] = score
            overall_scores.append(score)

        # Calculate Overall Score (Average of all category scores)
        if overall_scores:
            all_scores["overall_score"] = round(sum(overall_scores) / len(overall_scores), 2)
        else:
            all_scores["overall_score"] = 0.00

        return all_scores

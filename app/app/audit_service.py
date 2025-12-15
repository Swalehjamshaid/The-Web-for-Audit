# /app/app/audit_service.py

import random
# FIX: Use relative import for the sibling module audit_categories
from .audit_categories import AUDIT_CATEGORIES 

# Define the possible audit outcomes
AUDIT_STATUSES = ['Excellent', 'Good', 'Fair', 'Poor', 'N/A']

class AuditService:

    @staticmethod
    def _simulate_metric_check(metric_name: str) -> str:
        weights = [4, 4, 3, 2, 1] 
        return random.choices(AUDIT_STATUSES, weights=weights, k=1)[0]

    @staticmethod
    def run_audit(url: str):
        metrics_status_map = {}
        categories_result = {}

        for category, info in AUDIT_CATEGORIES.items():
            categories_result[category] = {"description": info["desc"], "items": []}
            
            for metric in info["metrics"]:
                status = AuditService._simulate_metric_check(metric)
                metrics_status_map[metric] = status
                categories_result[category]["items"].append({
                    "name": metric,
                    "status": status,
                    "suggestion": f"Check documentation for '{metric}'."
                })

        scores = AuditService.calculate_score(metrics_status_map)
        return {
            "url": url,
            "metrics_map": metrics_status_map,
            "categories": categories_result,
            "scores": scores
        }

    @staticmethod
    def calculate_score(metrics_status_map: dict) -> dict:
        def score_category(category_metrics_statuses: list) -> float:
            valid_metrics = [v for v in category_metrics_statuses if v != 'N/A']
            total_count = len(valid_metrics)
            if total_count == 0: return 0.00
            excellent = sum(1 for v in valid_metrics if v == 'Excellent')
            good = sum(0.5 for v in valid_metrics if v == 'Good')
            raw_score = (excellent + good) / total_count
            return round(raw_score * 100, 2)

        all_scores = {}
        category_scores_list = []
        
        for category, info in AUDIT_CATEGORIES.items():
            category_metrics_statuses = [
                metrics_status_map.get(metric, 'N/A')
                for metric in info["metrics"]
            ]
            score = score_category(category_metrics_statuses)
            score_key = f"{category.lower().replace(' ', '_')}_score"
            all_scores[score_key] = score
            category_scores_list.append(score)

        if category_scores_list:
            all_scores["overall_score"] = round(sum(category_scores_list) / len(category_scores_list), 2)
        else:
            all_scores["overall_score"] = 0.00

        return all_scores

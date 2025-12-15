import random
from audit_categories import AUDIT_CATEGORIES

class AuditService:

    @staticmethod
    def run_audit(url: str):
        metrics_result = {}
        categories_result = {}

        for cat, info in AUDIT_CATEGORIES.items():
            categories_result[cat] = {"desc": info["desc"], "items": info["metrics"]}
            for metric in info["metrics"]:
                metrics_result[metric] = random.choice(['Excellent','Good','Fair','Poor'])

        scores = AuditService.calculate_score(metrics_result)
        return {"metrics": metrics_result, "categories": categories_result, "scores": scores}

    @staticmethod
    def calculate_score(metrics):
        def score_category(cat_metrics):
            total = len(cat_metrics)
            excellent = sum(1 for v in cat_metrics if v=='Excellent')
            good = sum(1 for v in cat_metrics if v=='Good')
            return round((excellent + 0.5*good)/total*100,2)

        perf_metrics = [v for k,v in metrics.items() if k in AUDIT_CATEGORIES["Performance"]["metrics"]]
        sec_metrics = [v for k,v in metrics.items() if k in AUDIT_CATEGORIES["Security"]["metrics"]]
        acc_metrics = [v for k,v in metrics.items() if k in AUDIT_CATEGORIES["Accessibility"]["metrics"]]

        return {
            "performance_score": score_category(perf_metrics),
            "security_score": score_category(sec_metrics),
            "accessibility_score": score_category(acc_metrics),
            "all_scores": {}
        }

    @staticmethod
    def organize_metrics(metrics):
        data = {"metrics": metrics, "categories": {}}
        for cat, info in AUDIT_CATEGORIES.items():
            data["categories"][cat] = {"desc": info["desc"], "items": info["metrics"]}
        return data

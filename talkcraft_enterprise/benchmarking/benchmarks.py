from typing import Dict, List, Optional
from talkcraft_enterprise.utils.logger import get_logger

logger = get_logger("benchmarks")


BENCHMARK_CATEGORIES = {
    "speaking_pace": {
        "label": "Speaking Pace",
        "unit": "WPM",
        "ideal_range": [140, 170],
        "weights": {"wpm": 1.0},
    },
    "filler_control": {
        "label": "Filler Word Control",
        "unit": "%",
        "ideal_range": [0, 3],
        "weights": {"filler_rate": 1.0},
    },
    "grammar_accuracy": {
        "label": "Grammar Accuracy",
        "unit": "%",
        "ideal_range": [95, 100],
        "weights": {"grammar_accuracy": 1.0},
    },
    "eye_contact": {
        "label": "Eye Contact",
        "unit": "%",
        "ideal_range": [70, 100],
        "weights": {"eye_contact": 1.0},
    },
    "posture_stability": {
        "label": "Posture Stability",
        "unit": "%",
        "ideal_range": [70, 100],
        "weights": {"posture": 1.0},
    },
    "confidence": {
        "label": "Confidence",
        "unit": "%",
        "ideal_range": [70, 100],
        "weights": {"confidence": 1.0},
    },
    "overall_communication": {
        "label": "Overall Communication",
        "unit": "%",
        "ideal_range": [70, 100],
        "weights": {"overall": 0.3, "clarity": 0.2, "engagement": 0.2, "confidence": 0.15, "grammar": 0.15},
    },
}


ROLE_BENCHMARKS = {
    "software_engineer": {
        "label": "Software Engineer",
        "weightings": {"clarity": 0.3, "grammar_accuracy": 0.25, "speaking_pace": 0.2, "confidence": 0.15, "eye_contact": 0.1},
    },
    "product_manager": {
        "label": "Product Manager",
        "weightings": {"engagement": 0.3, "clarity": 0.25, "confidence": 0.2, "eye_contact": 0.15, "filler_control": 0.1},
    },
    "sales_executive": {
        "label": "Sales Executive",
        "weightings": {"confidence": 0.3, "engagement": 0.25, "eye_contact": 0.2, "speaking_pace": 0.15, "filler_control": 0.1},
    },
    "team_lead": {
        "label": "Team Lead / Manager",
        "weightings": {"clarity": 0.25, "engagement": 0.25, "confidence": 0.2, "posture_stability": 0.15, "eye_contact": 0.15},
    },
    "executive": {
        "label": "Executive / Director",
        "weightings": {"confidence": 0.3, "clarity": 0.25, "posture_stability": 0.2, "eye_contact": 0.15, "filler_control": 0.1},
    },
    "teacher_trainer": {
        "label": "Teacher / Trainer",
        "weightings": {"engagement": 0.3, "clarity": 0.25, "speaking_pace": 0.2, "eye_contact": 0.15, "confidence": 0.1},
    },
}


class BenchmarkEngine:
    def calculate_benchmarks(self, session_data: Dict) -> Dict:
        results = {}
        for bench_id, bench_info in BENCHMARK_CATEGORIES.items():
            score = self._calculate_category_score(bench_id, bench_info, session_data)
            ideal = bench_info["ideal_range"]
            status = "excellent" if score >= ideal[1] / 100 else ("good" if score >= ideal[0] / 100 else "needs_improvement")
            results[bench_id] = {
                "label": bench_info["label"],
                "score": round(score, 2),
                "unit": bench_info["unit"],
                "status": status,
                "ideal_range": ideal,
            }
        overall = results.get("overall_communication", {}).get("score", 0)
        return {
            "benchmarks": results,
            "overall": round(overall, 2),
            "overall_status": "excellent" if overall >= 0.8 else ("good" if overall >= 0.6 else "needs_improvement"),
        }

    def _calculate_category_score(self, bench_id: str, bench_info: Dict, data: Dict) -> float:
        scores = {}
        weights = bench_info["weights"]
        for metric, weight in weights.items():
            if metric == "overall":
                value = data.get("overall_score", 0) or (data.get("scores") or {}).get("overall", 0) or 0
            elif metric == "clarity":
                value = data.get("clarity_score", 0) or (data.get("scores") or {}).get("clarity", 0) or 0
            elif metric == "engagement":
                value = data.get("engagement_score", 0) or (data.get("scores") or {}).get("engagement", 0) or 0
            elif metric == "filler_rate":
                filler = data.get("filler_rate", 0)
                value = max(0, 1.0 - filler * 5)
            elif metric == "grammar_accuracy" or metric == "grammar":
                errors = data.get("grammar_errors", 0)
                words = data.get("word_count", 1)
                value = max(0, 1.0 - (errors / max(1, words)) * 10)
            elif metric == "eye_contact":
                value = data.get("average_eye_contact", 0) or data.get("eye_contact", 0) or (data.get("scores") or {}).get("eye_contact", 0) or 0
            elif metric == "posture":
                value = data.get("average_posture", 0) or data.get("posture", 0) or (data.get("scores") or {}).get("posture", 0) or 0
            elif metric == "confidence":
                value = data.get("confidence_score", 0) or data.get("confidence", 0) or (data.get("scores") or {}).get("confidence", 0) or 0
            elif metric == "wpm":
                wpm = data.get("average_wpm", 0) or data.get("avg_wpm", 0) or 0
                value = 1.0 if 140 <= wpm <= 170 else (0.8 if 120 <= wpm <= 190 else (0.6 if 100 <= wpm <= 210 else 0.3))
            else:
                value = data.get(metric, 0)
            if isinstance(value, dict):
                value = 0
            scores[metric] = value * weight
        total = sum(scores.values()) / sum(weights.values()) if weights else 0
        return min(1.0, total)

    def get_role_score(self, role_id: str, session_data: Dict) -> Dict:
        role = ROLE_BENCHMARKS.get(role_id)
        if not role:
            return {"error": f"Unknown role: {role_id}"}
        benchmarks = self.calculate_benchmarks(session_data)
        weighted_score = 0.0
        total_weight = 0.0
        details = {}
        for category, weight in role["weightings"].items():
            cat_score = benchmarks.get("benchmarks", {}).get(category, {}).get("score", 0)
            weighted_score += cat_score * weight
            total_weight += weight
            details[category] = {"score": cat_score, "weight": weight, "contribution": round(cat_score * weight, 2)}
        overall = weighted_score / total_weight if total_weight > 0 else 0
        return {
            "role_id": role_id,
            "role_name": role["label"],
            "overall_score": round(overall, 2),
            "category_scores": details,
            "recommendations": self._generate_role_recommendations(role_id, details),
        }

    def _generate_role_recommendations(self, role_id: str, details: Dict) -> List[str]:
        recs = []
        for category, info in details.items():
            if info["score"] < 0.6:
                bench = BENCHMARK_CATEGORIES.get(category, {})
                recs.append(f"Improve {bench.get('label', category)} (current: {info['score']*100:.0f}%)")
        return recs[:3]

    def calculate_percentile(self, user_score: float, all_scores: List[float]) -> float:
        if not all_scores:
            return 50.0
        below = sum(1 for s in all_scores if s < user_score)
        return round((below / len(all_scores)) * 100, 1)

    def get_role_list(self) -> List[Dict]:
        return [{"id": k, "label": v["label"]} for k, v in ROLE_BENCHMARKS.items()]


benchmark_engine = BenchmarkEngine()

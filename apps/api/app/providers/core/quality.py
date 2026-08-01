from app.providers.core.types import ProviderResult


def calculate_quality(result: ProviderResult) -> float:
    if result.records_received <= 0:
        return 0.0

    accepted = max(
        result.records_inserted + result.records_updated,
        result.records_validated - result.records_rejected,
    )
    completeness = min(accepted / result.records_received, 1.0)
    rejection_penalty = min(
        result.records_rejected / result.records_received,
        1.0,
    )
    error_penalty = min(len(result.errors) * 0.05, 0.5)
    warning_penalty = min(len(result.warnings) * 0.01, 0.15)

    score = (
        completeness * 100
        - rejection_penalty * 30
        - error_penalty * 100
        - warning_penalty * 100
    )
    return round(max(0.0, min(score, 100.0)), 2)

"""
EngageAI ML — feature_mapping/app_to_model.py

Maps live application activity events (database records) to the 70-feature
static vector + (40, 4) temporal sequence expected by the Bi-LSTM model.

DESIGN PHILOSOPHY:
  This module is scientifically honest about which features can be derived
  from application activity and which require onboarding data or fallbacks.
  See outputs/reports/live_activity_feature_mapping.txt for the full table.

FEATURE CATEGORIES:
  A) Derived directly from app activity (video clicks, quiz scores)
  B) Collected at onboarding (demographics, region, education level)
  C) Approximated from app context (module/course structure)
  D) Unavailable → use training-set median fallbacks (documented)
"""

import json
import numpy as np
from datetime import datetime, timedelta
from typing import List, Dict, Any
from sqlalchemy.orm import Session

# ─── Training-set median fallbacks (computed from target_dataset.csv) ────────
# These are used ONLY for features that cannot be derived from app activity.
# They represent the median values of the OULAD training population.
TRAINING_MEDIANS = {
    "num_of_prev_attempts"       : 0.0,
    "studied_credits"            : 60.0,
    "date_registration"          : -30.0,    # median registration offset (days before course start)
    "precourse_vle_clicks"       : 0.0,
    "first_interaction_day"      : 1.0,
    "last_interaction_day"       : 200.0,
    "late_submissions"           : 0.0,
    "banked_assessments"         : 0.0,
    "module_presentation_length" : 234.0,    # days
    "total_module_assessments"   : 4.0,
    "registration_delay"         : 0.0,
    "registered_before_course"   : 1.0,
    "late_registration_flag"     : 0.0,
    "is_repeat_student"          : 0.0,
    "credits_per_attempt"        : 60.0,
    "studied_credits_normalized" : 0.5,
}

# ─── Module presentation length (days) — used for normalization ──────────────
DEFAULT_COURSE_LENGTH = 234  # median across OULAD modules

# ─── Minimum activity threshold for a reliable prediction ───────────────────
MIN_EVENTS_FOR_PREDICTION = 5


def get_current_week_index(course_start_date: datetime | None = None) -> int:
    """
    Returns the current week index based on course start.
    If course_start_date is None, assumes the course has been running for 10 weeks.
    Week 0 = pre-course, Week 1-39 = course weeks.
    """
    if course_start_date is None:
        return 10  # safe default
    delta = (datetime.utcnow() - course_start_date).days
    if delta < 0:
        return 0
    return min(39, 1 + delta // 7)


def aggregate_weekly_sequence(
    activity_events: List[Any],
    course_start_date: datetime | None = None,
) -> np.ndarray:
    """
    Converts raw activity_events into a (40, 4) temporal sequence tensor.

    Each week w in [0..39] produces 4 features:
      [0] weekly_clicks_log      = log1p(total interaction count in week w)
      [1] active_days_in_week    = number of distinct days with activity in week w
      [2] interaction_frequency  = clicks_log / active_days (0 if no active days)
      [3] inactivity_indicator   = 1.0 if zero activity in week, 0.0 otherwise

    Application events contributing to "clicks":
      VIDEO_STARTED, VIDEO_PROGRESS, VIDEO_COMPLETED,
      QUIZ_STARTED, QUIZ_ANSWERED, QUIZ_COMPLETED,
      CONTENT_OPENED, CONTENT_COMPLETED
    """
    CLICK_EVENTS = {
        "VIDEO_STARTED", "VIDEO_PROGRESS", "VIDEO_COMPLETED",
        "QUIZ_STARTED", "QUIZ_ANSWERED", "QUIZ_COMPLETED",
        "CONTENT_OPENED", "CONTENT_COMPLETED",
    }

    # Initialize week buckets: {week_idx: {days: set, clicks: int}}
    weeks: Dict[int, Dict] = {w: {"clicks": 0, "days": set()} for w in range(40)}

    for event in activity_events:
        if event.event_type not in CLICK_EVENTS:
            continue

        # Determine week index from event timestamp
        if course_start_date is not None:
            delta_days = (event.timestamp - course_start_date).days
            if delta_days < 0:
                w_idx = 0  # pre-course
            else:
                w_idx = min(39, 1 + delta_days // 7)
        else:
            w_idx = event.week_index if event.week_index is not None else 1

        weeks[w_idx]["clicks"] += 1
        weeks[w_idx]["days"].add(event.timestamp.date())

    # Build (40, 4) tensor
    seq = np.zeros((40, 4), dtype=np.float32)
    for w in range(40):
        clicks      = weeks[w]["clicks"]
        active_days = len(weeks[w]["days"])

        seq[w, 0] = np.log1p(clicks)                                        # weekly_clicks_log
        seq[w, 1] = float(active_days)                                      # active_days_in_week
        seq[w, 2] = float(clicks) / active_days if active_days > 0 else 0.0 # interaction_frequency
        seq[w, 3] = 0.0 if clicks > 0 else 1.0                              # inactivity_indicator

    return seq  # shape (40, 4)


def build_static_features(
    activity_events: List[Any],
    quiz_attempts: List[Any],
    content_progress: List[Any],
    user_profile: dict,
) -> Dict[str, float]:
    """
    Builds the 34 numerical + 6 categorical raw feature dict expected
    by FeaturePreprocessor.transform().

    user_profile dict (collected at onboarding) should contain:
      gender, region, highest_education, imd_band, age_band, disability

    Returns a flat dict of all raw features (before preprocessing).
    """

    # ── A) FEATURES DERIVED FROM APP ACTIVITY ──────────────────────────────
    click_events = [
        e for e in activity_events if e.event_type in {
            "VIDEO_STARTED", "VIDEO_PROGRESS", "VIDEO_COMPLETED",
            "QUIZ_STARTED", "QUIZ_ANSWERED", "QUIZ_COMPLETED",
            "CONTENT_OPENED", "CONTENT_COMPLETED",
        }
    ]
    total_clicks = len(click_events)

    # Distinct active days
    active_days = len(set(e.timestamp.date() for e in click_events))

    # VLE-equivalent features
    avg_clicks_per_active_day = total_clicks / active_days if active_days > 0 else 0.0
    clicks_per_course_day     = total_clicks / DEFAULT_COURSE_LENGTH
    vle_activity_ratio        = min(1.0, active_days / DEFAULT_COURSE_LENGTH)
    interaction_intensity     = avg_clicks_per_active_day

    # Assessment-derived features
    n_attempts      = len(quiz_attempts)
    scores          = [a.score_pct for a in quiz_attempts if a.completed_at is not None]
    mean_score      = float(np.mean(scores)) if scores else 0.0
    min_score       = float(np.min(scores)) if scores else 0.0
    max_score       = float(np.max(scores)) if scores else 0.0
    late_subs       = sum(1 for a in quiz_attempts if a.completion_time and a.completion_time > 3600)
    assessment_completion_rate  = n_attempts / max(1, TRAINING_MEDIANS["total_module_assessments"])
    late_submission_ratio       = late_subs / max(1, n_attempts)
    assessment_score_normalized = mean_score / 100.0
    failed_flag     = 1.0 if mean_score < 40.0 and n_attempts > 0 else 0.0
    high_score_flag = 1.0 if mean_score >= 80.0 and n_attempts > 0 else 0.0
    assessment_performance_score = assessment_score_normalized * assessment_completion_rate

    # Content progress features
    completed_content = sum(1 for p in content_progress if p.is_completed)
    click_activity_score = min(1.0, total_clicks / 500.0)  # normalized 0–1

    # Engagement composite (mirrors original feature)
    overall_engagement_indicator = (
        0.4 * assessment_performance_score +
        0.3 * click_activity_score +
        0.3 * vle_activity_ratio
    )

    # ── B) DEMOGRAPHIC FEATURES (from onboarding profile) ──────────────────
    gender             = user_profile.get("gender", "M")
    region             = user_profile.get("region", "South East Region")
    highest_education  = user_profile.get("highest_education", "A Level or Equivalent")
    imd_band           = user_profile.get("imd_band", "50-60%")
    age_band           = user_profile.get("age_band", "0-35")
    disability         = user_profile.get("disability", "N")

    # ── C) COURSE/MODULE FEATURES (from profile or defaults) ──────────────
    studied_credits    = float(user_profile.get("studied_credits", TRAINING_MEDIANS["studied_credits"]))
    num_prev_attempts  = float(user_profile.get("num_of_prev_attempts", TRAINING_MEDIANS["num_of_prev_attempts"]))
    is_repeat_student  = 1.0 if num_prev_attempts > 0 else 0.0
    credits_per_attempt = studied_credits / max(1, num_prev_attempts + 1)
    studied_credits_normalized = min(1.0, studied_credits / 120.0)

    # ── D) UNAVAILABLE FEATURES → MEDIAN FALLBACKS (documented) ──────────
    date_registration         = TRAINING_MEDIANS["date_registration"]
    precourse_vle_clicks      = TRAINING_MEDIANS["precourse_vle_clicks"]
    first_interaction_day     = TRAINING_MEDIANS["first_interaction_day"]
    last_interaction_day      = float(active_days * 7) if active_days > 0 else TRAINING_MEDIANS["last_interaction_day"]
    late_submissions          = float(late_subs)
    banked_assessments        = TRAINING_MEDIANS["banked_assessments"]
    module_presentation_length = TRAINING_MEDIANS["module_presentation_length"]
    total_module_assessments  = TRAINING_MEDIANS["total_module_assessments"]
    registration_delay        = TRAINING_MEDIANS["registration_delay"]
    registered_before_course  = TRAINING_MEDIANS["registered_before_course"]
    late_registration_flag    = TRAINING_MEDIANS["late_registration_flag"]

    return {
        # Categorical (passed directly to OneHotEncoder)
        "gender"            : gender,
        "region"            : region,
        "highest_education" : highest_education,
        "imd_band"          : imd_band,
        "age_band"          : age_band,
        "disability"        : disability,

        # Numerical
        "num_of_prev_attempts"       : num_prev_attempts,
        "studied_credits"            : studied_credits,
        "date_registration"          : date_registration,
        "total_vle_clicks"           : float(total_clicks),
        "active_vle_days"            : float(active_days),
        "precourse_vle_clicks"       : precourse_vle_clicks,
        "first_interaction_day"      : first_interaction_day,
        "last_interaction_day"       : last_interaction_day,
        "assessments_submitted"      : float(n_attempts),
        "mean_score"                 : mean_score,
        "min_score"                  : min_score,
        "max_score"                  : max_score,
        "late_submissions"           : late_submissions,
        "banked_assessments"         : banked_assessments,
        "module_presentation_length" : module_presentation_length,
        "total_module_assessments"   : total_module_assessments,
        "avg_clicks_per_active_day"  : avg_clicks_per_active_day,
        "clicks_per_course_day"      : clicks_per_course_day,
        "vle_activity_ratio"         : vle_activity_ratio,
        "interaction_intensity"      : interaction_intensity,
        "registration_delay"         : registration_delay,
        "registered_before_course"   : registered_before_course,
        "late_registration_flag"     : late_registration_flag,
        "assessment_completion_rate" : assessment_completion_rate,
        "late_submission_ratio"      : late_submission_ratio,
        "assessment_score_normalized": assessment_score_normalized,
        "failed_assessment_flag"     : failed_flag,
        "high_score_flag"            : high_score_flag,
        "is_repeat_student"          : is_repeat_student,
        "credits_per_attempt"        : credits_per_attempt,
        "studied_credits_normalized" : studied_credits_normalized,
        "click_activity_score"       : click_activity_score,
        "assessment_performance_score": assessment_performance_score,
        "overall_engagement_indicator": overall_engagement_indicator,
    }


def has_sufficient_activity(activity_events: List[Any]) -> bool:
    """Returns True if there is enough activity for a meaningful prediction."""
    meaningful = [
        e for e in activity_events if e.event_type in {
            "VIDEO_STARTED", "VIDEO_COMPLETED", "QUIZ_COMPLETED",
            "CONTENT_COMPLETED",
        }
    ]
    return len(meaningful) >= MIN_EVENTS_FOR_PREDICTION

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

PLAN_STARTER = 'starter'
PLAN_PRO = 'pro'
PLAN_ENTERPRISE = 'enterprise'

PLAN_CHOICES = (
    (PLAN_STARTER, 'Starter'),
    (PLAN_PRO, 'Pro'),
    (PLAN_ENTERPRISE, 'Enterprise'),
)

PLAN_LABELS = {
    PLAN_STARTER: 'Starter',
    PLAN_PRO: 'Pro',
    PLAN_ENTERPRISE: 'Enterprise',
}


@dataclass(frozen=True)
class PlanLimits:
    document_limit: Optional[int]
    max_file_size_mb: Optional[int]
    max_user_queries: Optional[int]

    def as_dict(self) -> Dict[str, Optional[int]]:
        return {
            'document_limit': self.document_limit,
            'max_file_size_mb': self.max_file_size_mb,
            'max_user_queries': self.max_user_queries,
        }


PLAN_LIMITS: Dict[str, PlanLimits] = {
    PLAN_STARTER: PlanLimits(document_limit=10, max_file_size_mb=20, max_user_queries=50),
    PLAN_PRO: PlanLimits(document_limit=2000, max_file_size_mb=500, max_user_queries=None),
    PLAN_ENTERPRISE: PlanLimits(document_limit=None, max_file_size_mb=None, max_user_queries=None),
}


def normalize_plan(value: Optional[str]) -> str:
    if value in PLAN_LIMITS:
        return value  # type: ignore
    return PLAN_STARTER


def plan_label(plan: Optional[str]) -> str:
    return PLAN_LABELS.get(normalize_plan(plan), PLAN_LABELS[PLAN_STARTER])


def get_plan_limits(plan: Optional[str]) -> PlanLimits:
    return PLAN_LIMITS.get(normalize_plan(plan), PLAN_LIMITS[PLAN_STARTER])


def get_effective_plan_and_source(user) -> Tuple[str, Optional[str]]:
    profile = getattr(user, 'userprofile', None)
    if profile is None:
        return PLAN_STARTER, None

    org = getattr(profile, 'organization', None)
    if org:
        plan = normalize_plan(getattr(org, 'plan', None))
        return plan, 'organization'

    plan = normalize_plan(getattr(profile, 'plan', None))
    return plan, 'profile'


def get_effective_plan(user) -> str:
    plan, _ = get_effective_plan_and_source(user)
    return plan


def serialize_plan(plan: Optional[str]) -> Dict[str, Optional[int]]:
    code = normalize_plan(plan)
    limits = get_plan_limits(code).as_dict()
    return {
        'code': code,
        'label': plan_label(code),
        'limits': limits,
    }


def can_manage_plan(user) -> bool:
    profile = getattr(user, 'userprofile', None)
    if profile is None:
        return False
    if getattr(profile, 'account_type', 'individual') == 'individual':
        return True
    return getattr(profile, 'role', '') == 'org_owner'

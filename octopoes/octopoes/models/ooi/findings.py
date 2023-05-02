import abc
from enum import Enum, StrEnum
from typing import Literal, Optional

from pydantic import AnyUrl

from octopoes.models import OOI, Reference
from octopoes.models.persistence import ReferenceField


class RiskLevelSeverity(StrEnum):
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    RECOMMENDATION = "recommendation"


class FindingType(OOI, abc.ABC):
    id: str

    description: Optional[str]
    source: Optional[AnyUrl]

    risk_score: Optional[float]
    risk_severity: Optional[RiskLevelSeverity]

    _natural_key_attrs = ["id"]
    _information_value = ["id"]
    _traversable = False

    @classmethod
    def format_reference_human_readable(cls, reference: Reference) -> str:
        return reference.tokenized.id


class ADRFindingType(FindingType):
    object_type: Literal["ADRFindingType"] = "ADRFindingType"


class CVEFindingType(FindingType):
    object_type: Literal["CVEFindingType"] = "CVEFindingType"


class CWEFindingType(FindingType):
    object_type: Literal["CWEFindingType"] = "CWEFindingType"


class CAPECFindingType(FindingType):
    object_type: Literal["CAPECFindingType"] = "CAPECFindingType"


class RetireJSFindingType(FindingType):
    object_type: Literal["RetireJSFindingType"] = "RetireJSFindingType"


class SnykFindingType(FindingType):
    object_type: Literal["SnykFindingType"] = "SnykFindingType"


class KATFindingType(FindingType):
    object_type: Literal["KATFindingType"] = "KATFindingType"


class Finding(OOI):
    object_type: Literal["Finding"] = "Finding"

    finding_type: Reference = ReferenceField(FindingType)
    ooi: Reference = ReferenceField(OOI)
    proof: Optional[str]
    description: Optional[str]
    reproduce: Optional[str]

    @property
    def natural_key(self) -> str:
        return f"{str(self.ooi)}|{self.finding_type.natural_key}"

    _reverse_relation_names = {"ooi": "findings", "finding_type": "instances"}

    @classmethod
    def format_reference_human_readable(cls, reference: Reference) -> str:
        parts = reference.natural_key.split("|")
        finding_type = parts.pop()
        ooi_reference = Reference.from_str("|".join(parts))
        return f"{finding_type} @ {ooi_reference.human_readable}"


class MutedFinding(OOI):
    object_type: Literal["MutedFinding"] = "MutedFinding"

    finding: Reference = ReferenceField(Finding)
    reason: Optional[str]

    _natural_key_attrs = ["finding"]
    _reverse_relation_names = {"finding": "mutes"}

    @classmethod
    def format_reference_human_readable(cls, reference: Reference) -> str:
        return f"Muted {reference.natural_key}"

"""
Pydantic validation models for the two-agent prescription pipeline:

1. OCRExtractionOutput   -> validates the OCR/transcription subagent's output
2. CoordinatorVerificationOutput -> validates the fact-verification coordinator's output

Both agents should be prompted to return JSON matching these schemas
(via tool-use / structured output), and the app code should call
`Model.model_validate(raw_output)` immediately after each agent call —
never trust raw LLM output past this boundary.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import (
    BaseModel,
    Field,
    HttpUrl,
    field_validator,
    model_validator,
)


# ---------------------------------------------------------------------------
# Shared enums / constants
# ---------------------------------------------------------------------------

NOT_SPECIFIED = "Not specified"
ILLEGIBLE = "Illegible"
_ALLOWED_MISSING_VALUES = {NOT_SPECIFIED, ILLEGIBLE}


class VerificationStatus(str, Enum):
    VERIFIED = "true"
    NOT_VERIFIED = "false"
    NEEDS_REVIEW = "needs_review"


class DiagnosisAlignment(str, Enum):
    CONSISTENT = "consistent"
    INCONSISTENT = "inconsistent"
    UNRELATED_BUT_PLAUSIBLE = "unrelated_but_plausible"
    NOT_APPLICABLE = "not_applicable"


class InteractionSeverity(str, Enum):
    NONE = "none"
    MINOR = "minor"
    SIGNIFICANT = "significant"
    UNKNOWN = "unknown"


def _is_missing_placeholder(value: str) -> bool:
    return value.strip() in _ALLOWED_MISSING_VALUES


# ---------------------------------------------------------------------------
# 1. OCR Extraction Subagent output
# ---------------------------------------------------------------------------

class PatientInfo(BaseModel):
    name: str = NOT_SPECIFIED
    age_or_dob: str = NOT_SPECIFIED
    sex: str = NOT_SPECIFIED


class PrescriberInfo(BaseModel):
    doctor_name: str = NOT_SPECIFIED
    clinic_or_hospital: str = NOT_SPECIFIED
    registration_or_license_number: str = NOT_SPECIFIED
    contact_details: str = NOT_SPECIFIED


class MedicationEntry(BaseModel):
    drug_name_as_written: str
    strength_dosage: str = NOT_SPECIFIED
    form: str = NOT_SPECIFIED
    frequency_timing: str = NOT_SPECIFIED
    duration: str = NOT_SPECIFIED
    quantity: str = NOT_SPECIFIED
    context_assisted: bool = Field(
        default=False,
        description=(
            "True if any field in this entry was resolved using the "
            "patient-reported diagnosis context per the OCR agent's rules, "
            "rather than being clearly legible on its own."
        ),
    )

    @field_validator("drug_name_as_written")
    @classmethod
    def drug_name_required(cls, v: str) -> str:
        # Drug name is the one field that must never be silently blank —
        # if illegible, the agent must still write "Illegible", not omit it.
        v = v.strip()
        if not v:
            raise ValueError(
                "drug_name_as_written must not be empty — use 'Illegible' "
                "if the drug name cannot be read."
            )
        return v


class OCRExtractionOutput(BaseModel):
    patient_information: PatientInfo
    prescriber_information: PrescriberInfo
    date: str = NOT_SPECIFIED
    medications: list[MedicationEntry] = Field(default_factory=list)
    special_instructions: str = NOT_SPECIFIED
    diagnosis_indication: str = NOT_SPECIFIED
    is_valid_prescription_image: bool = Field(
        default=True,
        description="False if the image was not a prescription or too degraded to transcribe.",
    )
    rejection_reason: Optional[str] = Field(
        default=None,
        description="Populated only when is_valid_prescription_image is False.",
    )

    @model_validator(mode="after")
    def check_rejection_consistency(self) -> "OCRExtractionOutput":
        if not self.is_valid_prescription_image and not self.rejection_reason:
            raise ValueError(
                "rejection_reason is required when is_valid_prescription_image is False."
            )
        if self.is_valid_prescription_image and not self.medications:
            # Not a hard error — a prescription could legitimately have zero
            # readable medications — but this is exactly the case that should
            # route to manual review downstream, so we don't silently allow it
            # to look like a normal empty list without a diagnosis-only note.
            if _is_missing_placeholder(self.diagnosis_indication):
                raise ValueError(
                    "No medications extracted and no diagnosis/indication noted — "
                    "this likely indicates a failed extraction, not an empty "
                    "prescription. Flag for manual review instead of returning "
                    "this as a normal result."
                )
        return self


# ---------------------------------------------------------------------------
# 2. Coordinator (Tavily fact-verification) output
# ---------------------------------------------------------------------------

class MedicationVerification(BaseModel):
    drug_name_as_written: str
    verified: VerificationStatus
    confidence: float = Field(ge=0.0, le=1.0)
    diagnosis_alignment: DiagnosisAlignment
    sources: list[HttpUrl] = Field(default_factory=list)
    notes: str

    @field_validator("notes")
    @classmethod
    def notes_required(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("notes must explain what was checked — never leave blank.")
        return v

    @model_validator(mode="after")
    def require_sources_when_verified(self) -> "MedicationVerification":
        # A claim marked VERIFIED with zero sources is exactly the failure
        # mode the coordinator's system prompt is designed to prevent
        # ("never state a claim is verified without a supporting source").
        # Enforce it structurally, don't just rely on the prompt.
        if self.verified == VerificationStatus.VERIFIED and not self.sources:
            raise ValueError(
                f"'{self.drug_name_as_written}' marked verified=true but has no "
                "sources. Every verified claim must cite at least one search result."
            )
        return self

    @model_validator(mode="after")
    def confidence_status_consistency(self) -> "MedicationVerification":
        # Guard against an agent saying "verified" with low confidence, or
        # "needs_review" with suspiciously high confidence — these usually
        # indicate the model didn't actually reconcile the two fields.
        if self.verified == VerificationStatus.VERIFIED and self.confidence < 0.5:
            raise ValueError(
                f"'{self.drug_name_as_written}' marked verified=true but confidence "
                f"({self.confidence}) is below 0.5 — use 'needs_review' instead."
            )
        if self.verified == VerificationStatus.NOT_VERIFIED and self.confidence < 0.5:
            # NOT_VERIFIED can legitimately have low confidence (we're confident
            # it's wrong) or could indicate ambiguity — allow, but this is a
            # good spot to log for eval calibration rather than hard-reject.
            pass
        return self


class InteractionFlag(BaseModel):
    drugs_involved: list[str] = Field(min_length=2)
    severity: InteractionSeverity
    sources: list[HttpUrl] = Field(default_factory=list)
    notes: str

    @model_validator(mode="after")
    def require_sources_for_flagged_severity(self) -> "InteractionFlag":
        if self.severity in (InteractionSeverity.MINOR, InteractionSeverity.SIGNIFICANT) and not self.sources:
            raise ValueError(
                f"Interaction flagged as '{self.severity.value}' between "
                f"{self.drugs_involved} but has no supporting sources."
            )
        return self


class CoordinatorVerificationOutput(BaseModel):
    medications: list[MedicationVerification] = Field(default_factory=list)
    interaction_flags: list[InteractionFlag] = Field(default_factory=list)
    unverifiable_fields: list[str] = Field(default_factory=list)

    @property
    def requires_manual_review(self) -> bool:
        """
        Convenience property the LangGraph node can check directly to decide
        whether to route to `needs_manual_review` vs. proceed to the
        reviewer's normal queue.
        """
        any_needs_review = any(
            m.verified == VerificationStatus.NEEDS_REVIEW for m in self.medications
        )
        any_not_verified = any(
            m.verified == VerificationStatus.NOT_VERIFIED for m in self.medications
        )
        any_inconsistent_diagnosis = any(
            m.diagnosis_alignment == DiagnosisAlignment.INCONSISTENT for m in self.medications
        )
        any_significant_interaction = any(
            f.severity == InteractionSeverity.SIGNIFICANT for f in self.interaction_flags
        )
        return (
            any_needs_review
            or any_not_verified
            or any_inconsistent_diagnosis
            or any_significant_interaction
            or bool(self.unverifiable_fields)
        )


# ---------------------------------------------------------------------------
# Usage example
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Example: validating raw agent output (e.g. from a tool-use response)
    raw_ocr_output = {
        "patient_information": {"name": "Jane Doe", "age_or_dob": "34F", "sex": "F"},
        "prescriber_information": {
            "doctor_name": "Dr. A. Kumar",
            "clinic_or_hospital": "City Clinic",
            "registration_or_license_number": "Illegible",
            "contact_details": "Not specified",
        },
        "date": "12-06-2026",
        "medications": [
            {
                "drug_name_as_written": "Amoxicillin",
                "strength_dosage": "500mg",
                "form": "tablet",
                "frequency_timing": "tds",
                "duration": "5 days",
                "quantity": "15",
                "context_assisted": False,
            }
        ],
        "special_instructions": "Take after food",
        "diagnosis_indication": "Throat infection",
        "is_valid_prescription_image": True,
    }

    ocr_result = OCRExtractionOutput.model_validate(raw_ocr_output)
    print(ocr_result.model_dump_json(indent=2))

    raw_coordinator_output = {
        "medications": [
            {
                "drug_name_as_written": "Amoxicillin",
                "verified": "true",
                "confidence": 0.92,
                "diagnosis_alignment": "consistent",
                "sources": ["https://www.drugs.com/amoxicillin.html"],
                "notes": "Standard antibiotic for throat infection; dosage within typical adult range.",
            }
        ],
        "interaction_flags": [],
        "unverifiable_fields": ["registration_or_license_number"],
    }

    coordinator_result = CoordinatorVerificationOutput.model_validate(raw_coordinator_output)
    print(coordinator_result.model_dump_json(indent=2))
    print("requires_manual_review:", coordinator_result.requires_manual_review)

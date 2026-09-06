import os
from typing import Optional

from dotenv import load_dotenv
from langchain.tools import tool
from langchain_tavily import TavilyResearch
from pydantic import BaseModel, Field

load_dotenv()


class PrescriptionInput(BaseModel):
    prescription: Optional[str] = Field(
        default=None,
        description="The full text or details of the prescription to verify against clinical guidelines.",
    )
    prescription_data: Optional[str] = Field(
        default=None,
        description="The full text or details of the prescription to verify against clinical guidelines.",
    )


_research = TavilyResearch(
    model="auto",
)


@tool("verify_prescription", args_schema=PrescriptionInput)
def verify_prescription(
    prescription: Optional[str] = None, prescription_data: Optional[str] = None
) -> str:
    """Verify prescription medication name, dosage, interactions and clinical
    guidelines using medical literature."""
    value = prescription or prescription_data
    if not value:
        raise ValueError("Prescription data cannot be empty.")

    
    res = _research.invoke({"input": value})
    return str(res)
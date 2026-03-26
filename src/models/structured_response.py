from typing import List

from pydantic import BaseModel, Field


class CodeComment(BaseModel):
    """Model that holds the structure for a specific comment on a file."""

    file_name: str = Field(description="Relative file path of specific file")
    line_number: int = Field(description="Line number for comment")
    review: str = Field(description="Suggestions provided by LLM to improve code")


class CodeReview(BaseModel):
    """Model that holds the structure for agent response."""

    score: int = Field(description="Score out of 100")
    summary: str = Field(description="Summary of PR changes")
    comments: List[CodeComment] = Field(description="List of all comments in PR")
    summarized_comments: str = Field(
        description="Summary of all comments for user to view"
    )

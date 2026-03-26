from typing import List, Optional

from pydantic import BaseModel, Field


class CodeComment(BaseModel):
    """Model that holds the structure for a specific comment on a file."""

    file_name: str = Field(description="Relative file path of specific file")
    line_number: int = Field(description="Line number for comment")
    review: str = Field(description="Suggestions provided by LLM to improve code")


#class CodeReview(BaseModel):
#    """Model that holds the structure for agent response."""
#
 #   score: int = Field(description="Score out of 100")
  #  summary: str = Field(description="Summary of PR changes")
   # comments: List[CodeComment] = Field(description="List of all comments in PR")
    #summarized_comments: str = Field(
     #   description="Summary of all comments for user to view"
    #)

class ReviewerResponse(BaseModel):
    """Structured response from the Code Reviewer agent for a single hunk."""

    needs_comment: bool = Field(description="Whether a comment is warranted")
    severity: str = Field(
        description="Severity level of the issue",
        pattern="^(nit|minor|major|blocker)$",
    )
    issue: str = Field(description="Description of the identified issue")
    impact: str = Field(description="Impact of the issue on code quality")
    ask_coder: bool = Field(
        description="Whether to delegate fix generation to the coding agent"
    )
    coder_request: Optional[str] = Field(
        default=None, description="Precise request for coder if ask_coder is True"
    )
    suggestion: Optional[str] = Field(
        default=None, description="Initial suggestion or placeholder"
    )
    line: int = Field(description="Line number where comment should be placed")


class CoderResponse(BaseModel):
    """Structured response from the Coding agent."""

    snippet: str = Field(description="The code fix or implementation snippet")
    rationale: str = Field(description="Explanation of the fix")

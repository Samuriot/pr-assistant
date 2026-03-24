from pydantic import BaseModel, Field
from typing import List

class CodeComment(BaseModel):
    '''Model that will hold the structure for a specific comment on a file'''
    file_name: str = Field(description="Relative file path of specific file")
    line_number: int = Field(description="Line number for comment")
    review: str = Field(desciription="Suggestions provided by LLM to improve code")

class CodeReview(BaseModel):
    '''Model that will hold the structure for agent response'''
    score: int = Field(description="Score out of 100")
    summary: str = Field(description="Summary of PR changes")
    comments: List[CodeComment] = Field("List of all comments in PR")
    summarized_comments: str = Field("Summary of all comments for user to view")


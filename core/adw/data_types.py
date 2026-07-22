"""Typed models for the ADW system.

The Literal types here are not decoration. `IssueClass` is the *return type* of the
/classify_issue slash command, and `ValidationVerdict` of /validate — an agent's free
text is validated against them before the pipeline advances. A model that answers
outside the enum fails the run loudly instead of corrupting a later step.
"""

from datetime import datetime
from typing import List, Literal, Optional

from pydantic import BaseModel, Field

# Return type of /classify_issue. Must match the planning commands the harness installs.
IssueClass = Literal["/plan_chore", "/plan_bug", "/plan_feature"]

# Every slash command the ADW pipeline is allowed to invoke.
SlashCommand = Literal[
    "/classify_issue",
    "/generate_branch_name",
    "/find_plan_file",
    "/validate",
    "/plan_chore",
    "/plan_bug",
    "/plan_feature",
    "/implement",
]


class GitHubUser(BaseModel):
    login: str
    id: Optional[str] = None
    name: Optional[str] = None
    is_bot: bool = Field(default=False, alias="is_bot")


class GitHubLabel(BaseModel):
    id: Optional[str] = None
    name: str
    color: Optional[str] = None
    description: Optional[str] = None


class GitHubComment(BaseModel):
    id: Optional[str] = None
    author: Optional[GitHubUser] = None
    body: str = ""
    created_at: Optional[datetime] = Field(None, alias="createdAt")


class GitHubIssue(BaseModel):
    number: int
    title: str
    body: str = ""
    state: str = "OPEN"
    author: GitHubUser
    labels: List[GitHubLabel] = []
    comments: List[GitHubComment] = []
    url: str = ""
    created_at: Optional[datetime] = Field(None, alias="createdAt")

    class Config:
        populate_by_name = True

    def as_prompt(self) -> str:
        """The issue rendered as the prompt body for a planning command."""
        return f"{self.title}\n\n{self.body}".strip()


class AgentTemplateRequest(BaseModel):
    """One slash-command invocation of Claude Code, as its own fresh process."""

    agent_name: str
    slash_command: SlashCommand
    args: List[str] = []
    adw_id: str
    model: str = "sonnet"
    # cwd for the claude process — the run's worktree. None falls back to the
    # repo root (pre-worktree nodes like /classify_issue, which only read the issue).
    working_dir: Optional[str] = None


class AgentPromptResponse(BaseModel):
    output: str
    success: bool
    session_id: Optional[str] = None


ValidationVerdict = Literal["PASS", "FAIL"]


class ValidationResult(BaseModel):
    """Outcome of the /validate gate. `verdict` decides whether a PR may be opened."""

    verdict: ValidationVerdict
    detail: str = ""

    @property
    def passed(self) -> bool:
        return self.verdict == "PASS"

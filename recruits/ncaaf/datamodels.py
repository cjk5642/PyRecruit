from msilib.schema import Class
from optparse import Option
from typing import Optional, Union, NewType, List, Protocol
from dataclasses import dataclass
import pandas as pd

DataFrame = NewType('DataFrame', pd.DataFrame)
collegeinterest = NewType("CollegeInterest", Protocol)
pedigree = NewType('Connections', Protocol)
recruiter = NewType('StaffMember', Protocol)
top_commit = NewType("TopCommit", Protocol)
coach_history = NewType("CoachHistory", Protocol)

@dataclass
class PlayerDC:
    name_id: str
    url: str
    recruit_name: str
    pos: str
    height: str
    weight: int
    high_school: str
    city: str
    state: str
    class_year: int
    composite_score: float = None
    national_composite_rank: int = None
    position_composite_rank: int = None
    state_composite_rank: int = None
    normal_score: int = None
    national_normal_rank: int = None
    position_normal_rank: int = None
    state_normal_rank: int = None
    experts:dict = None
    college_interest: Union[List[collegeinterest], collegeinterest, None] = None
    accolades: list = None
    evaluators: dict = None
    background: str = None
    skills: dict = None
    stats: DataFrame = None
    connections: Union[List[pedigree], pedigree, None] = None

@dataclass
class Evaluator:
    id: int
    name: str
    region: str
    projection: str
    comparison: Union[str, None]
    comparison_team: Union[str, None]
    evaluation_date: str
    evaluation: str

@dataclass
class Connection:
    name: str
    relation: str
    accolades: Union[list, str]
    
@dataclass
class CollegeInterest:
    college: str
    status: Union[str, None]
    status_date: Union[str, None]
    visit: Union[str, None]
    offered: Union[bool, None]
    recruited_by: List[recruiter] = None

@dataclass
class StaffMember:
    name: str
    position: str = None
    alma_mater: str = None
    college: str = None
    staff_member_age: int = None
    top_commits: Union[List[top_commit], top_commit, None] = None
    coach_history: Union[List[coach_history], coach_history, None] = None
    commits: Optional[int] = None
    avg_rtg: Optional[float] = None
    natl_rk: Optional[int] = None
    star_5: Optional[int] = None
    star_4: Optional[int] = None
    star_3: Optional[int] = None
    conference: Optional[str] = None


@dataclass
class TopCommit:
    name: str
    location: str
    position: str
    height: str
    weight: str
    stars: int
    rating: float
    college: str
    commitment_date: str

@dataclass
class CoachHistory:
    college: str
    year: str
    position: str


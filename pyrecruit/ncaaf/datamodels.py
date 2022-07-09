from typing import Optional, Union, NewType, List
from dataclasses import dataclass
import pandas as pd

DataFrame = NewType('DataFrame', pd.DataFrame)

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
class CoachHistory:
    college: str
    year: str
    position: str

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
class StaffMember:
    name: str
    position: str = None
    alma_mater: str = None
    college: str = None
    staff_member_age: int = None
    top_commits: Union[List[TopCommit], TopCommit, None] = None
    coach_history: Union[List[CoachHistory], CoachHistory, None] = None
    commits: Optional[int] = None
    avg_rtg: Optional[float] = None
    natl_rk: Optional[int] = None
    star_5: Optional[int] = None
    star_4: Optional[int] = None
    star_3: Optional[int] = None
    conference: Optional[str] = None

@dataclass
class CollegeInterest:
    college: str
    status: Union[str, None]
    status_date: Union[str, None]
    visit: Union[str, None]
    offered: Union[bool, None]
    recruited_by: List[StaffMember] = None

@dataclass
class Expert:
    name: str
    expert_score: str
    prediction: str
    prediction_datetime: str = None
    title: str = None
    accuracy_year: float = None
    accuracy_all_time: float = None

@dataclass
class Ratings:
    composite_score: float = None
    national_composite_rank: int = None
    position_composite_rank: int = None
    state_composite_rank: int = None
    normal_score: int = None
    national_normal_rank: int = None
    position_normal_rank: int = None
    state_normal_rank: int = None

@dataclass(init=False)
class Skills:

    @classmethod
    def from_kwargs(cls, **kwargs):
        ret = cls()
        for new_name, new_val in kwargs.items():
            setattr(ret, new_name, new_val)
        return ret

@dataclass
class PlayerPreview:
    id: str
    name: str
    link: str
    high_school: str
    location: str
    position: str
    height: str
    weight: str
    primary_ranking: Union[int, None] = None
    other_ranking: Union[int, None] = None
    national_rank: Union[int, None] = None
    position_rank: Union[int, None] = None
    state_rank: Union[int, None] = None
    commitment1: Union[str, None] = None
    committed_team_percentage1: Union[float, None] = None
    commitment2: Union[str, None] = None
    committed_team_percentage2: Union[float, None] = None


@dataclass
class PlayerExtended:
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
    ratings: Union[Ratings, None] = None
    experts: Union[List[Expert], Expert, None] = None
    college_interest: Union[List[CollegeInterest], CollegeInterest, None] = None
    accolades: list = None
    evaluators: dict = None
    background: str = None
    skills: dict = None
    stats: DataFrame = None
    connections: Union[List[Connection], Connection, None] = None
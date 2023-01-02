"""Script housing all of the dataclasses used 
across the project.
"""

from dataclasses import dataclass, field, asdict
import pandas as pd
from pandas import DataFrame

@dataclass
class Evaluator:
    """Evaluator Dataclass
    """
    id: int
    name: str
    region: str
    projection: str
    comparison: str
    comparison_team: str
    evaluation_date: str
    evaluation: str

@dataclass
class Connection:
    """Connection dataclass
    """
    name: str
    relation: str
    accolades: list[str] | str

@dataclass
class CoachHistory:
    """History of the Coach dataclass
    """
    college: str
    year: str
    position: str

@dataclass
class TopCommit:
    """Top Commit dataclass
    """
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
    """Staff Member dataclass
    """
    name: str
    position: str = None
    alma_mater: str = None
    college: str = None
    staff_member_age: int = None
    top_commits: list[TopCommit] | TopCommit = None
    coach_history: list[CoachHistory] | CoachHistory = None
    commits: int = None
    avg_rtg: float = None
    natl_rk: int = None
    star_5: int = None
    star_4: int = None
    star_3: int = None
    conference: str = None

@dataclass
class CollegeInterest:
    """College Interest of the player dataclass
    """
    college: str
    status: str
    status_date: str
    visit: str
    offered: bool
    recruited_by: list[StaffMember] = None

@dataclass
class Expert:
    """Expert Dataclass
    """
    name: str
    expert_score: str
    prediction: str
    prediction_datetime: str = None
    title: str = None
    accuracy_year: float = None
    accuracy_all_time: float = None

@dataclass
class Ratings:
    """Ratings dataclass
    """
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
    """Skills dataclass of the player
    """

    @classmethod
    def from_kwargs(cls, **kwargs):
        """Method to allow extra parameters to the dataclass

        Returns:
            ret: class parameters that were added to the dataclass
        """
        ret = cls()
        for new_name, new_val in kwargs.items():
            setattr(ret, new_name, new_val)
        return ret

@dataclass
class AbstractPlayer:
    name_id: str
    recruit_name: str
    url: str
    position: str
    height: str
    weight: str
    high_school: str = None
    class_year: int = None
    city: str = None
    state: str = None

@dataclass
class PlayerPreview:
    """An overview of Recruit dataclass
    """
    abstract_player: AbstractPlayer
    primary_ranking: int = None
    other_ranking: int = None
    national_rank: int = None
    position_rank: int = None
    state_rank: int = None
    commitment1: str = None
    committed_team_percentage1: float = None
    commitment2: str = None
    committed_team_percentage2: float = None


@dataclass
class PlayerExtended:
    """Detailed information on the Recruit dataclass
    """
    abstract_player: AbstractPlayer
    ratings: Ratings = None
    experts: list[Expert] | Expert = None
    college_interest: list[CollegeInterest] | CollegeInterest = None
    accolades: list = None
    evaluators: dict = None
    background: str = None
    skills: dict = None
    stats: DataFrame = None
    connections: list[Connection] | Connection = None

@dataclass
class PlayerCrystalBall:
    """Crystal Ball predictions of Recruit dataclass
    """
    abstract_player: AbstractPlayer
    stars: int
    rating: str
    predictor_id: str
    predictor_name: str
    predictor_link: str
    predictor_affiliation: str
    predictor_accuracy: str
    prediction_team: str
    prediction_datetime: str
    confidence_score: int
    confidence_text: str
    vip_scoop: bool

@dataclass
class PlayersDC:
    players: list[PlayerPreview] = field(default_factory=dataclass)

    @property
    def dataframe(self) -> pd.DataFrame:
        """Method to extract the players as dataframe.

        Returns:
            pd.DataFrame: Pandas dataframe of all the players.
        """
        return pd.DataFrame.from_dict([asdict(p) for p in self.players])

@dataclass
class CrystalballPlayersDC:
    players: list[PlayerCrystalBall] = field(default_factory=dataclass)

    @property
    def dataframe(self) -> pd.DataFrame:
        """Send results to the DataFrame

        Returns:
            pd.DataFrame: _description_
        """
        return pd.DataFrame.from_dict([asdict(p) for p in self.players])

@dataclass
class TeamPreview:
    """Overview of Team recruiting dataclass
    """
    team_id: str
    team_name: str
    primary_ranking: int = None
    other_ranking: int = None
    total_commiits: int = None
    team_avg: float = None
    team_points: float = None
    five_star: int = None
    four_star: int = None
    three_star: int = None
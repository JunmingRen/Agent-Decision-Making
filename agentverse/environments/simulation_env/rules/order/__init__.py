from agentverse.registry import Registry
order_registry = Registry(name="OrderRegistry")

from .base import BaseOrder
from .sequential import SequentialOrder
from .random import RandomOrder
from .concurrent import ConcurrentOrder
from .classroom import ClassroomOrder
from .prisoner import PrisonerOrder
from .sde_team import SdeTeamOrder
from .sde_team_given_tests import SdeTeamGivenTestsOrder
from .misinformation_6players import Misinformation6PlayersOrder
from .misinformation import Misinformation10PlayersOrder
from .consistency_test import ConsistencyTestOrder
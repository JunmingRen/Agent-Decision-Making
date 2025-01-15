from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, List, Optional

from . import order_registry as OrderRegistry
from .base import BaseOrder
from agentverse.logging import logger

if TYPE_CHECKING:
    from agentverse.environments import BaseEnvironment, MisinformationEnvironment


@OrderRegistry.register("misinformation_6players")
class Misinformation6PlayersOrder(BaseOrder):
    """The order for misinformation in 6-player simulation.
    The agents speak in the following order:
    1. As the host, the professor leads turns
    2. Team_A students speak in turn, and Team_B students should answer do they believe
    3. The professor can call on a student, then the student can speak or ask a question
    4. In the group discussion, the students in the group can speak in turn
    """
    current_presentor: Optional[int] = None

    def get_next_agent_idx(self, environment: MisinformationEnvironment) -> List[int]:
        agent_cnt = len(environment.agents)
        if len(environment.last_messages) == 0 and environment.agents[0].current_action == "":
            # If the class just begins , we let only the professor speak
            return [0]
        elif len(environment.last_messages) == 1:
            message = environment.last_messages[0]
            sender = message.sender
            content = message.content
            if sender.startswith("Professor"):
                if content.startswith("[CallOn]"):
                    # 1. professor calls on someone, then the student should speak
                    result = re.search(r"\[CallOn\] Yes, ([sS]tudent )?(\w+)", content)
                    if result is not None:
                        name_to_id = {
                            agent.name[len("Student ") :]: i
                            for i, agent in enumerate(environment.agents)
                        }
                        # update the current_presentor
                        self.current_presentor = name_to_id[result.group(2)]
                        environment.update_presenting(self.current_presentor)
                        return [self.current_presentor]
                elif content.startswith("[Query]"):
                    # 2. professor asks do they believe ...
                    print("Querying")
                    return [num for num in range(1, agent_cnt) if num != self.current_presentor]
                    # return the ids of students who are not the current_presentor
                else:
                    return list(range(1, agent_cnt))
            elif sender.startswith("Student"):
                # 3. student finishes its presentation
                if content.startswith("[Present]"):
                    environment.update_presenting(self.current_presentor)
                if content.startswith("[MoveToFront]") or content.startswith("[Present]"):
                    return [self.current_presentor]
                else:
                    return [0]
        else:
            # If len(last_messages) > 1, then there must be 5 students respond to the last presentation.
            # We let the professor speak again.
            return [0]
        assert (
            False
        ), f"Should not reach here, last_messages: {environment.last_messages}"

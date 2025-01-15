from __future__ import annotations

from typing import TYPE_CHECKING, List

from agentverse.message import Message

from . import selector_registry as SelectorRegistry
from .base import BaseSelector

if TYPE_CHECKING:
    from agentverse.environments import BaseEnvironment, MisinformationEnvironment


@SelectorRegistry.register("misinformation_10players")
class Misinformation10PlayersSelector(BaseSelector):
    def select_message(
        self, environment: MisinformationEnvironment, messages: List[Message]
    ) -> List[Message]:
        selected = []
        for message in messages:
            current_agent = environment.get_agent_by_name(message.sender)
            current_action = environment.get_action_by_agent(current_agent)
            if message.sender.startswith("Student"):
                if environment.agents[0].current_action == "CallOn":
                    if environment.is_called_on(current_agent) and message.content.startswith("[MoveToFront]"):
                        selected.append(message)
                        environment.update_action_by_agent(current_agent, "MoveToFront")
                    if environment.is_called_on(current_agent) and message.content.startswith("[Present]"):
                        selected.append(message)
                        environment.update_action_by_agent(current_agent, "Present")
                if environment.agents[0].current_action == "Query" :
                    if message.content.startswith("[Respond]"):
                        selected.append(message)
                        environment.update_action_by_agent(current_agent, "Respond")
                    else:
                        print(f"Error: {message.sender} sent {message.content} while in Query state. Expected [Respond]")
                        message.content = "[Listen]"
                        selected.append(message)
                        environment.update_action_by_agent(current_agent, "Listen")

                # if current_action == "Respond":
                #     environment.update_action_by_agent(current_agent, "Listen")

                # if message.content.startswith("[Listen]"):
                #     selected.append(message)
                #     environment.update_action_by_agent(current_agent, "Listen")
            elif message.sender.startswith("Professor"):
                print(f"Pro: {message.sender} sent {message.content} while in {current_action} state.")
                if current_action == "":
                    selected.append(message)
                    environment.update_action_by_agent(current_agent, "CallOn")
                elif current_action == "CallOn" and message.content.startswith("[Query]"):
                    selected.append(message)
                    environment.update_action_by_agent(current_agent, "Query")
                elif current_action == "Query" and message.content.startswith("[CallOn]"):
                    selected.append(message)
                    environment.update_action_by_agent(current_agent, "CallOn")
                else:
                    environment.update_action_by_agent(current_agent, "Query")
                

        # If some student speak while the professor is speaking, then
        # we brutely discard the student's message in this turn
        if (
            len(selected) > 1
            and selected[0].sender.startswith("Professor")
            and selected[0].content != ""
        ):
            filtered_selected = []
            filtered_selected.append(selected[0])
            for message in selected[1:]:
                if message.content.startswith("[RaiseHand]"):
                    filtered_selected.append(message)
            selected = filtered_selected
        return selected

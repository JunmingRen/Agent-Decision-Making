from __future__ import annotations

from typing import TYPE_CHECKING, List, Tuple

from . import updater_registry as UpdaterRegistry
from .basic import BasicUpdater
from agentverse.message import Message

if TYPE_CHECKING:
    from agentverse.environments import MisinformationEnvironment

import os

@UpdaterRegistry.register("misinformation_6players")
class Misinformation6PlayersUpdater(BasicUpdater):
    def update_memory(self, environment: MisinformationEnvironment):
        # 确保目录存在
        output_dir = "./output_records"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        added = False
        for message in environment.last_messages:
            if len(message.tool_response) > 0:
                self.add_tool_response(
                    message.sender, environment.agents, message.tool_response
                )
            if message.content == "":
                continue
            agent = environment.get_agent_by_name(message.sender)
            if agent.current_action == "Respond" :
                output_filename = output_dir + environment.output_filename
                with open(output_filename, "a") as f:
                    sender = message.sender
                    if message.content.startswith("[Respond]"):
                        output_part = message.content.split("[Respond]")[1].strip()
                        output = f"{sender} {output_part}\n"
                    else:
                        output = f"{sender} [Listen]\n"
                    f.write(output)
                # Split the content to remove the [Think] part
                respond_part = message.content.split("[Think]")[0].strip()
                message.content = respond_part
            added |= self.add_message_to_all_agents(environment.agents, message)
        # If no one speaks in this turn. Add an empty message to all agents
        if not added:
            for agent in environment.agents:
                agent.add_message_to_memory([Message(content="[Silence]")])

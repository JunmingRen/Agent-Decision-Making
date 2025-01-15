import asyncio

# import logging
from agentverse.logging import get_logger
from typing import Any, Dict, List

# from agentverse.agents.agent import Agent
from agentverse.agents.simulation_agent.misinformation import MisinformationAgent

# from agentverse.environments.simulation_env.rules.base import Rule
from agentverse.environments.simulation_env.rules.base import SimulationRule as Rule
from agentverse.message import Message

logger = get_logger()

from .. import env_registry as EnvironmentRegistry
from ..base import BaseEnvironment

from datetime import datetime


@EnvironmentRegistry.register("misinformation")
class MisinformationEnvironment(BaseEnvironment):
    """
    A basic environment implementing the logic of conversation.

    Args:
        agents: List of agents
        rule: Rule for the environment
        max_turns: Maximum number of turns
        cnt_turn: Current turn number
        last_messages: Messages from last turn
        rule_params: Variables set by the rule
    """

    agents: List[MisinformationAgent]
    rule: Rule
    max_turns: int = 10
    cnt_turn: int = 0
    last_messages: List[Message] = []
    rule_params: Dict = {}
    output_filename: str = ""
    is_presenting: Dict[int, bool] = {}

    def __init__(self, rule, **kwargs):
        rule_config = rule
        order_config = rule_config.get("order", {"type": "sequential"})
        visibility_config = rule_config.get("visibility", {"type": "all"})
        selector_config = rule_config.get("selector", {"type": "basic"})
        updater_config = rule_config.get("updater", {"type": "basic"})
        describer_config = rule_config.get("describer", {"type": "basic"})
        rule = Rule(
            order_config,
            visibility_config,
            selector_config,
            updater_config,
            describer_config,
        )
        super().__init__(rule=rule, **kwargs)

        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_filename = f"/misinfo_10players_{current_time}.txt"

    async def step(self) -> List[Message]:
        """Run one step of the environment"""

        # Get the next agent index
        agent_ids = self.rule.get_next_agent_idx(self)
        print(f"Agent IDs: {agent_ids}")

        # Generate current environment description
        env_descriptions = self.rule.get_env_description(self)

        # Generate the next message
        messages = await asyncio.gather(
            *[self.agents[i].astep(env_descriptions[i]) for i in agent_ids]
        )

        # Some rules will select certain messages from all the messages
        selected_messages = self.rule.select_message(self, messages)
        self.last_messages = selected_messages
        self.print_messages(selected_messages)

        # Update the memory of the agents
        self.rule.update_memory(self)

        # Update the set of visible agents for each agent
        self.rule.update_visible_agents(self)

        self.cnt_turn += 1

        return selected_messages
    
    def print_messages(self, messages: List[Message]) -> None:
        for message in messages:
            if message is not None:
                # logging.info(f"{message.sender}: {message.content}")
                logger.info(f"{message.sender}: {message.content}")

    def reset(self) -> None:
        """Reset the environment"""
        self.cnt_turn = 0
        self.rule.reset()
        for agent in self.agents:
            agent.reset()

    def is_done(self) -> bool:
        """Check if the environment is done"""
        return self.cnt_turn >= self.max_turns or self.agents[10].visited
    
    def get_agent_by_name(self, name: str) -> MisinformationAgent:
        for agent in self.agents:
            if agent.name == name:
                return agent
        return None
    
    def get_action_by_agent(self, agent: MisinformationAgent) -> str:
        for agent_index, a in enumerate(self.agents):
            if a == agent:
                return self.agents[agent_index].current_action
    
    def is_called_on(self, agent: MisinformationAgent) -> bool:
        for agent_index, a in enumerate(self.agents):
            if a == agent:
                return self.is_presenting.get(agent_index, False)
    
    def update_presenting(self, agent_index: int) -> None:
        self.is_presenting[agent_index] = not self.is_presenting.get(agent_index, False)
    
    def update_action_by_agent(self, agent: MisinformationAgent, action: str) -> None:
        for agent_index, a in enumerate(self.agents):
            if a == agent:
                self.agents[agent_index].current_action = action

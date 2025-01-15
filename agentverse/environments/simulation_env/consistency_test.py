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


@EnvironmentRegistry.register("consistency_test")
class ConsistencyTestEnvironment(BaseEnvironment):
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
    is_checking: bool = True

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
        self.output_filename = f"/consistency_test_{current_time}.txt"

    async def step(self) -> List[Message]:
        """Run one step of the environment"""
        # Get the next agent index
        agent_ids = self.rule.get_next_agent_idx(self)
        print(f"Agent IDs: {agent_ids}")

        # Generate current environment description
        env_descriptions = self.rule.get_env_description(self)

        if self.is_checking:
            await self.consistency_check(env_descriptions=env_descriptions)
            self.is_checking = False

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

    async def consistency_check(self, env_descriptions: List[Dict[str, Any]]) -> None:
        output_dir = "./output_records"
        output_filename = output_dir + self.output_filename
        for i, agent in enumerate(self.agents):
            questions = """
                Now, there are some statements for you. To answer each question, use only one number for each: 
                write 1 if you disagree strongly, 
                write 2 if you disagree a little, 
                write 3 if you neither agree nor disagree, 
                write 4 if you agree a little,
                write 5 if you strongly agree. 
                Write only one number according to the instructions WITHOUT ANY ADDITIONAL TEXT.
            """
            if i == 0:
                continue
            if i == 1 or i == 2:
                questions += """
                1. Do you enjoy trying new things, such as new foods or activities?
                2. Do you usually have an open attitude towards different viewpoints?
                3. Do you enjoy engaging in creative activities such as painting or writing?
                4. Are you excited about new ideas instead of afraid?
                """
            elif i == 3 or i == 4:
                questions += """
                1. Are you a well-organized person who can manage your time well? 
                2. Do you tend to conscientiously complete tasks without procrastinating? 
                3. Do you often make plans and strive to achieve goals?
                4. Will you carefully consider the consequences before making a decision?
                """
            elif i == 5 or i == 6:
                questions += """
                1. Do you enjoy talking to people and establishing new social connections? 
                2. Are you usually an active participant at parties? 
                3. Do you often take the initiative to organize events or gatherings? 
                4. Do you enjoy performing or speaking in public places?
                """
            elif i == 7 or i == 8:
                questions += """
                1. Do you tend to pay attention to others' feelings and be willing to help them?
                2. Do you always try to avoid arguments or conflicts with others?
                3. Do you easily trust others and tend to forgive them?
                4. Do you prefer working with others rather than going it alone?
                """
            elif i == 9 or i == 10:
                questions += """
                1. Can you handle stress well and maintain emotional stability?
                2. Do you rarely feel anxious or worried? 
                3. Can you remain calm when facing difficulties? 
                4. Do you usually feel confident about the challenges in life, rather than fearful?
                """
            message = await self.agents[i].astep_check(env_descriptions[i], questions) 
            
            with open(output_filename, "a") as f:
                f.write(f"Agent {i}:\n")
                print(f"{message.sender}:\n{message.content}\n")
                f.write(f"{message.sender}: {message.content}\n")
            print(f"Agent {i} done.")
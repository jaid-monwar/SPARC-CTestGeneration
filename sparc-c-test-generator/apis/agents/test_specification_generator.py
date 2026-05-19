from apis.gpt import GPT_Connection
from apis.agents.vectordb_manager import VectorDBManager
from apis.agents.operation_map_manager import OperationMapManager
from apis.agents.test_scenarios_manager import TestScenariosManager
from apis.agents.test_validator import TestValidator


class TestSpecificationGenerator:
    def __init__(self):
        self.gpt_connection = GPT_Connection()
        self.vector_db_manager = VectorDBManager()
        self.op_map_manager = OperationMapManager(self.vector_db_manager)
        self.test_scenario_manager = TestScenariosManager()
        self.test_validator = TestValidator()

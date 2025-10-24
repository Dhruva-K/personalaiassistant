# filepath: langgraph-agent/src/config/config.py
# Configuration settings for the agent

class Config:
    TOOL_TIMEOUT = 5  # seconds
    MAX_RETRIES = 3
    DEFAULT_TOOL = "default_tool"
    STATE_TRANSITION_TIMEOUT = 10  # seconds
    LOGGING_LEVEL = "INFO"  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL

    @staticmethod
    def get_tool_timeout():
        return Config.TOOL_TIMEOUT

    @staticmethod
    def get_max_retries():
        return Config.MAX_RETRIES

    @staticmethod
    def get_default_tool():
        return Config.DEFAULT_TOOL

    @staticmethod
    def get_state_transition_timeout():
        return Config.STATE_TRANSITION_TIMEOUT

    @staticmethod
    def get_logging_level():
        return Config.LOGGING_LEVEL
from deriv.core.config import settings

def test_settings_load():
    """
    Verify that settings can be loaded and have default values.
    """
    assert settings.LOG_LEVEL in ["DEBUG", "INFO", "WARNING", "ERROR"]
    assert isinstance(settings.DEBUG, bool)

def test_config_structure():
    """
    Check if the settings object has the expected keys.
    """
    assert hasattr(settings, "OPENAI_API_KEY")
    assert hasattr(settings, "ANTHROPIC_API_KEY")

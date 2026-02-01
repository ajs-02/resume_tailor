"""Configuration constants for Resume Tailor application."""

# API Configuration
API_KEY_NAMES = {
    "google": "GEMINI_API_KEY",
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY"
}

# Model Configuration
MODELS = {
    "google": "gemini-2.0-flash",
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-latest"
}

# LLM Parameters
LLM_TEMPERATURE = 0.2

# Rate Limiting
FREE_TIER_MAX_REQUESTS = 3

# Scraper Configuration
SCRAPER_CONFIG = {
    "verbose": True,
    "magic": True,
    "bypass_cache": True,
    "word_count_threshold": 10
}

# UI Configuration
STREAMLIT_CONFIG = {
    "page_title": "Resume Tailor",
    "page_icon": None,
    "layout": "wide"
}

# PDF Export Configuration
PDF_CONFIG = {
    "font_family": "Arial",
    "encoding": "latin-1",
    "font_sizes": {
        "name": 16,
        "section_title": 12,
        "job_title": 11,
        "body": 10,
        "error": 12
    },
    "auto_page_break": True,
    "margin": 15
}

# File Paths
STYLE_CSS = "style.css"

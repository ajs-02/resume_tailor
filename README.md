# Resume Tailor

AI-powered resume optimization system with multi-provider LLM support.

## Overview

Resume Tailor is a Streamlit-based web application that uses large language models to tailor resumes to specific job descriptions. The system extracts job requirements from URLs, analyzes resume content, and generates optimized versions that emphasize relevant experience and keywords for ATS compatibility.

The application implements a provider-agnostic architecture supporting Google Gemini, OpenAI GPT-4o, and Anthropic Claude through a unified interface.

## Tech Stack

**Backend:**
- Python 3.12
- LangChain (LLM abstraction layer)
- Google Generative AI SDK
- OpenAI Python SDK
- Anthropic Python SDK

**Frontend:**
- Streamlit (web UI)

**Data Processing:**
- pypdf (PDF text extraction)
- fpdf (PDF generation)
- crawl4ai (async web scraping with Playwright)

**Infrastructure:**
- python-dotenv (environment configuration)
- asyncio (async job scraping)

## Architecture

### Factory Pattern for LLM Providers

The `ResumeTailor` class uses a factory pattern to abstract provider-specific implementations:

```python
class ResumeTailor:
    def __init__(self, provider="google", api_key=None):
        self.provider = provider
        self.api_key = api_key
        self.llm = self._create_llm()

    def _create_llm(self):
        if self.provider == "google":
            return ChatGoogleGenerativeAI(model=MODELS["google"], temperature=LLM_TEMPERATURE)
        elif self.provider == "openai":
            return ChatOpenAI(model=MODELS["openai"], temperature=LLM_TEMPERATURE)
        elif self.provider == "anthropic":
            return ChatAnthropic(model=MODELS["anthropic"], temperature=LLM_TEMPERATURE)
```

**Design Benefits:**
- Single interface for multiple LLM providers
- Runtime provider selection without code changes
- Centralized configuration via `config.py`
- Easy to extend with additional providers

### Component Architecture

```
src/
├── config.py        # Centralized configuration (models, API keys, constants)
├── app.py           # Streamlit UI and application orchestration
├── tailor.py        # LLM provider factory and prompt engineering
├── scraper.py       # Async job description scraper (crawl4ai + Playwright)
├── ingest.py        # PDF text extraction
├── exporter.py      # PDF generation with ATS-optimized layout
└── old_tailor.py    # Legacy implementation (Google Gemini SDK)
```

### Data Flow

1. User uploads PDF resume and provides job URL
2. `ingest.py` extracts text from PDF using pypdf
3. `scraper.py` fetches and parses job description via crawl4ai
4. `tailor.py` sends resume + job description to selected LLM provider
5. LLM returns structured JSON with optimized resume sections
6. `exporter.py` generates ATS-compatible PDF from structured data

### Configuration Management

All magic strings and hardcoded values are extracted to `src/config.py`:

- `MODELS`: Model identifiers for each provider
- `API_KEY_NAMES`: Environment variable mappings
- `LLM_TEMPERATURE`: Temperature parameter for all providers
- `FREE_TIER_MAX_REQUESTS`: Rate limiting threshold
- `SCRAPER_CONFIG`: crawl4ai parameters
- `PDF_CONFIG`: Font sizes, encoding, layout settings

## Setup

### Prerequisites

- Python 3.12 or higher
- Conda or venv
- At least one LLM provider API key

### Installation

```bash
# Clone repository
git clone <repository-url>
cd Resume_Project

# Create virtual environment
conda create -n resume_tailor python=3.12
conda activate resume_tailor

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers (required for crawl4ai)
playwright install chromium
```

### Configuration

Create `.env` file in project root:

```env
GEMINI_API_KEY=<your-key>
OPENAI_API_KEY=<your-key>
ANTHROPIC_API_KEY=<your-key>
```

At least one API key is required. Obtain keys from:
- Google Gemini: https://aistudio.google.com/app/apikey
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

## Usage

### Running the Application

```bash
streamlit run src/app.py
```

Application launches at `http://localhost:8501`

### Testing Components

```bash
# Test PDF extraction
python src/ingest.py

# Test web scraper
python src/scraper.py

# Test LLM connection
python src/tailor.py

# List available Gemini models
python src/check_models.py
```

## Implementation Details

### Rate Limiting

Session-based rate limiting restricts free-tier usage to 3 requests per session. Users can bypass limits by providing their own API keys. Counter persists across Streamlit reruns via `st.session_state`.

### Prompt Engineering

The system uses a structured prompt that enforces JSON output with specific schema requirements:
- Executive summary lists specific changes made (not candidate profile)
- Strict field validation with fallback to empty values
- Double-brace escaping for JSON schema in prompt template

### PDF Generation

PDF export uses fpdf with:
- Latin-1 encoding (Unicode characters converted to ASCII equivalents)
- Single-column ATS-optimized layout
- Configurable font sizes via `PDF_CONFIG`
- Automatic page breaks with 15mm margins

### Windows Compatibility

- Explicit UTF-8 encoding for stdout/stderr
- WindowsProactorEventLoopPolicy for asyncio operations
- Cross-platform path handling via `os.path.join()`

## Known Limitations

- Free tier limited to 3 requests per session (by design)
- PDF export restricted to Latin-1 encoding (no emoji support)
- Web scraper requires Playwright-compatible browser
- No persistent storage (session state only)
- Single-user application (no authentication)

## Future Improvements

### High Priority
- **Unit Tests**: Add pytest suite for core modules (tailor, scraper, exporter)
- **Docker Containerization**: Create Dockerfile with multi-stage build for deployment
- **Database Integration**: Replace session state with SQLite/PostgreSQL for persistence
- **API Endpoint**: Expose REST API alongside Streamlit UI

### Medium Priority
- **Caching Layer**: Implement Redis for LLM response caching
- **Batch Processing**: Support multiple resumes/jobs in single session
- **Template System**: Allow users to define custom resume templates
- **Metrics Dashboard**: Track usage, success rates, and provider performance

### Low Priority
- **Multi-language Support**: Extend beyond English resumes
- **PDF Parsing Improvements**: Handle complex layouts and tables
- **Provider Cost Tracking**: Monitor API usage and costs per provider

## Dependencies

| Library | Version | Purpose |
|---------|---------|---------|
| `streamlit` | Latest | Web UI framework |
| `langchain-core` | Latest | LLM abstraction layer |
| `langchain-google-genai` | Latest | Google Gemini integration |
| `langchain-openai` | Latest | OpenAI GPT integration |
| `langchain-anthropic` | Latest | Anthropic Claude integration |
| `google-generativeai` | Latest | Direct Gemini API access |
| `crawl4ai` | Latest | Async web scraping |
| `pypdf` | Latest | PDF text extraction |
| `fpdf` | Latest | PDF generation |
| `python-dotenv` | Latest | Environment variable management |

## Author

Amanjeet Singh

- LinkedIn: https://linkedin.com/in/aj-singh02

## License

Available for portfolio and educational purposes.

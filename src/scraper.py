import sys

import requests
from bs4 import BeautifulSoup

from config import SCRAPER_CONFIG


class JobScraper:
    """Web scraper for job postings using BeautifulSoup."""

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': SCRAPER_CONFIG["user_agent"],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0'
        })

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.session.close()

    def scrape_job(self, url: str) -> str:
        """Scrape job posting URL and return text content.

        Args:
            url: Job posting URL

        Returns:
            Extracted text content from the page

        Raises:
            Exception: If scraping fails
        """
        try:
            print(f"[INFO] Scraping URL: {url}", flush=True)

            response = self.session.get(
                url,
                timeout=SCRAPER_CONFIG["timeout"],
                allow_redirects=True
            )
            response.raise_for_status()

            soup = BeautifulSoup(response.content, 'html.parser')

            for script in soup(["script", "style", "nav", "footer", "header"]):
                script.decompose()

            text = soup.get_text(separator='\n', strip=True)
            lines = [line.strip() for line in text.splitlines() if line.strip()]
            content = '\n'.join(lines)

            if len(content) < SCRAPER_CONFIG["min_content_length"]:
                raise Exception(f"Content too short ({len(content)} chars). Site may require JavaScript.")

            print(f"[INFO] Successfully scraped {url} ({len(content)} chars)", flush=True)
            return content

        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 401:
                error_msg = (
                    f"Access denied by {url}. This site blocks automated scraping. "
                    "Please copy and paste the job description manually into a text file, "
                    "or try a different job posting URL."
                )
            else:
                error_msg = f"HTTP {e.response.status_code} error scraping {url}: {str(e)}"
            print(f"[ERROR] {error_msg}", flush=True)
            raise Exception(error_msg)
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error scraping {url}: {str(e)}"
            print(f"[ERROR] {error_msg}", flush=True)
            raise Exception(error_msg)
        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            print(f"[ERROR] {error_msg}", flush=True)
            raise Exception(error_msg)


def main():
    """Test scraper functionality."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    test_url = "https://www.python.org/jobs/"

    print("-" * 50)
    print("[INFO] Starting JobScraper test...")
    print("-" * 50)

    try:
        with JobScraper() as scraper:
            content = scraper.scrape_job(test_url)

            print(f"\n[INFO] Content length: {len(content)} chars")
            print("[INFO] Preview (first 500 chars):")
            print("-" * 20)
            print(content[:500])
            print("-" * 20)

    except Exception as e:
        print(f"[ERROR] Test execution failed: {e}")
        return 1

    print("\n[INFO] Test finished.")
    return 0


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

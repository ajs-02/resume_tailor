import asyncio
import sys

from crawl4ai import AsyncWebCrawler

from config import SCRAPER_CONFIG


class JobScraper:
    """Async web scraper for job postings using crawl4ai."""

    def __init__(self):
        self.crawler = None

    async def __aenter__(self):
        self.crawler = AsyncWebCrawler(verbose=SCRAPER_CONFIG["verbose"])
        await self.crawler.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.crawler:
            await self.crawler.__aexit__(exc_type, exc_val, exc_tb)

    async def scrape_job(self, url: str) -> str:
        """Scrape job posting URL and return markdown content."""
        try:
            print(f"[INFO] Scraping URL: {url}", flush=True)

            result = await self.crawler.arun(
                url=url,
                magic=SCRAPER_CONFIG["magic"],
                bypass_cache=SCRAPER_CONFIG["bypass_cache"],
                word_count_threshold=SCRAPER_CONFIG["word_count_threshold"],
            )

            if result.success:
                print(f"[INFO] Successfully scraped {url}", flush=True)
                return result.markdown
            else:
                error_msg = f"Failed to scrape {url}: {result.error_message}"
                print(f"[ERROR] {error_msg}", flush=True)
                raise Exception(error_msg)

        except Exception as e:
            error_msg = f"Error scraping {url}: {str(e)}"
            print(f"[ERROR] {error_msg}", flush=True)
            raise Exception(error_msg)


async def main():
    """Test scraper functionality."""
    if sys.platform == "win32":
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    test_url = "https://google.com"

    print("-" * 50)
    print("[INFO] Starting JobScraper test...")
    print("-" * 50)

    try:
        async with JobScraper() as scraper:
            markdown_content = await scraper.scrape_job(test_url)

            print(f"\n[INFO] Content length: {len(markdown_content)} chars")
            print("[INFO] Preview (first 500 chars):")
            print("-" * 20)
            print(markdown_content[:500])
            print("-" * 20)

    except Exception as e:
        print(f"[ERROR] Test execution failed: {e}")
        return 1

    print("\n[INFO] Test finished.")
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
import os
import sys

# Ensure project root is on sys.path for direct execution
CURRENT_DIR = os.path.dirname(__file__)
PROJECT_ROOT = os.path.dirname(CURRENT_DIR)
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from app import create_app
from app.extensions import db
from app.models.scraper import ScrapedWebsite, ScrapeLog
from app.services.scraper_service import scrape_website


def main():
    url = os.environ.get('TEST_SCRAPE_URL', 'https://aitr.ac.in/')
    app = create_app()
    with app.app_context():
        site = ScrapedWebsite.query.filter_by(url=url).first()
        if not site:
            site = ScrapedWebsite(url=url)
            db.session.add(site)
            db.session.commit()

        ok, status = scrape_website(site)

        last_log = (
            ScrapeLog.query.filter_by(website_id=site.id)
            .order_by(ScrapeLog.scraped_at.desc())
            .first()
        )

        print('SCRAPE_RESULT:', {'ok': ok, 'status': status})
        if last_log:
            print(
                'LAST_LOG:',
                {
                    'status': last_log.status,
                    'text_len': last_log.extracted_text_length or 0,
                    'pdfs': last_log.pdf_links_found or 0,
                    'scraped_at': str(last_log.scraped_at),
                },
            )
        else:
            print('LAST_LOG: None')

        # Also persist to a file if terminal output is lost
        try:
            out_path = os.path.join(os.path.dirname(__file__), 'test_scrape_output.txt')
            with open(out_path, 'w', encoding='utf-8') as fh:
                fh.write(f"URL: {url}\n")
                fh.write(f"SCRAPE_RESULT: ok={ok}, status={status}\n")
                if last_log:
                    fh.write(
                        f"LAST_LOG: status={last_log.status}, text_len={last_log.extracted_text_length or 0}, pdfs={last_log.pdf_links_found or 0}, scraped_at={str(last_log.scraped_at)}\n"
                    )
                else:
                    fh.write("LAST_LOG: None\n")
        except Exception:
            pass


if __name__ == '__main__':
    main()

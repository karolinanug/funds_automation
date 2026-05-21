#!/usr/bin/env python3
"""
Swedbank pension fund sizes scraper - extracts fund size (Fondo dydis) data.
"""
import sys
from pathlib import Path

# Add parent directory to path so we can import base_scraper
sys.path.insert(0, str(Path(__file__).parent.parent))

from base_scraper import BaseScraper


class SwedBankFundSizesScraper(BaseScraper):
    """Scrapes Swedbank pension fund sizes."""
    
    def __init__(self):
        super().__init__("swedbank_fondo_dydis")
    
    def get_url(self) -> str:
        return "https://www.swedbank.lt/private/pensions/pillar2/allFunds?language=LIT"
    
    def dismiss_cookie_modal(self, page):
        """Aggressively dismiss all cookie modal buttons."""
        print("Dismissing cookie modal...")
        for attempt in range(5):
            try:
                buttons = page.query_selector_all('ui-cookie-consent button')
                for btn in buttons:
                    try:
                        btn.click(force=True)
                    except Exception:
                        pass
                page.wait_for_timeout(300)
            except Exception:
                pass
    
    def scrape_data(self, page) -> list:
        """Extract fund sizes by navigating to each fund's detail page."""
        results = []
        
        page.wait_for_timeout(2000)
        self.dismiss_cookie_modal(page)
        
        # Wait until fund list loads
        print("Waiting for fund rows...")
        page.wait_for_selector("tbody tr", timeout=60000)
        
        fund_rows = page.query_selector_all("tbody tr")
        print(f"Found {len(fund_rows)} funds")
        
        for index in range(len(fund_rows)):
            try:
                # Re-select rows every time (page may change)
                fund_rows = page.query_selector_all("tbody tr")
                if index >= len(fund_rows):
                    print(f"Row {index} no longer available, stopping.")
                    break
                
                row = fund_rows[index]
                cells = row.query_selector_all("td")
                
                # First cell is checkbox, second is fund name
                if len(cells) < 2:
                    continue
                
                fund_name = cells[1].inner_text().strip()
                if "tradicin" in fund_name.lower():
                    print(f"[{index+1}/{len(fund_rows)}] Skipping traditional fund: {fund_name}")
                    continue
                print(f"[{index+1}/{len(fund_rows)}] Opening fund: {fund_name}")
                
                # Click the link inside the fund name cell
                link = row.query_selector("a")
                if not link:
                    print(f"  No link found, skipping")
                    continue
                
                link.click(timeout=15000, force=True)
                
                # Wait for details panel to appear
                try:
                    # Wait for the page to navigate or content to load
                    page.wait_for_load_state("networkidle", timeout=30000)
                    page.wait_for_selector("text=Fondo dydis", timeout=30000)
                except Exception as e:
                    print(f"  Warning: Details panel did not load: {e}")
                    print(f"  Current URL: {page.url}")
                    try:
                        page.go_back()
                        page.wait_for_selector("tbody tr", timeout=30000)
                    except Exception as back_err:
                        print(f"  Failed to go back: {back_err}")
                    continue
                
                # Find all elements containing "Fondo dydis"
                detail_blocks = page.query_selector_all("div")
                
                fondo_dydis_value = None
                
                for block in detail_blocks:
                    try:
                        text = block.inner_text().strip()
                        
                        if text.startswith("Fondo dydis"):
                            # Example: "Fondo dydis (2026-04-16)\n123 456 789 EUR"
                            lines = text.split("\n")
                            
                            if len(lines) >= 2:
                                fondo_dydis_value = lines[1]
                            
                            break
                    except Exception:
                        continue
                
                results.append({
                    "Fund name": fund_name,
                    "Fondo dydis value": fondo_dydis_value
                })
                
                # Go back to fund list
                page.go_back()
                page.wait_for_selector("tbody tr", timeout=30000)
                page.wait_for_timeout(1000)
            
            except Exception as e:
                print(f"  Error processing row {index}: {e}")
                try:
                    page.go_back()
                    page.wait_for_selector("tbody tr", timeout=30000)
                except Exception:
                    pass
                continue
        
        return results


if __name__ == "__main__":
    scraper = SwedBankFundSizesScraper()
    scraper.run()

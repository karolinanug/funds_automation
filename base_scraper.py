#!/usr/bin/env python3
"""
Base class for pension fund scrapers.
Provides shared functionality for browser setup, error handling, and file output.
"""
from playwright.sync_api import sync_playwright
import pandas as pd
from datetime import datetime
from pathlib import Path
import sys
from abc import ABC, abstractmethod


class BaseScraper(ABC):
    """Abstract base class for pension fund scrapers."""
    
    def __init__(self, source_name: str):
        """
        Initialize scraper.
        
        Args:
            source_name: Name of the data source (e.g., 'swedbank')
        """
        self.source_name = source_name
        self.results = []
        self.browser = None
        self.page = None
    
    @abstractmethod
    def get_url(self) -> str:
        """Return the URL to scrape."""
        pass
    
    @abstractmethod
    def scrape_data(self, page) -> list:
        """
        Scrape data from the page. Subclasses must implement this.
        
        Args:
            page: Playwright page object
            
        Returns:
            List of dictionaries with scraped data
        """
        pass
    
    def setup_browser(self):
        """Initialize browser and page."""
        print("Starting browser...")
        p = sync_playwright().start()
        self.browser = p.chromium.launch(headless=True)
        self.page = self.browser.new_page()
        return self.page
    
    def cleanup_browser(self):
        """Close browser if open."""
        if self.browser:
            self.browser.close()
    
    def save_to_excel(self, df: pd.DataFrame, filename: str) -> str:
        """
        Save DataFrame to Excel file.
        
        Args:
            df: DataFrame to save
            filename: Output filename
            
        Returns:
            Full path to created file
        """
        if df.empty:
            print(f"No data to save for {self.source_name}.")
            return None
        
        filepath = Path(filename)
        df.to_excel(filepath, index=False)
        return str(filepath)
    
    def run(self):
        """
        Main execution method. Handles browser lifecycle and error handling.
        
        Returns:
            Path to created Excel file, or None if failed
        """
        try:
            # Setup
            self.setup_browser()
            
            # Scrape
            url = self.get_url()
            print(f"Opening: {url}")
            self.page.goto(url, timeout=60000)
            
            self.results = self.scrape_data(self.page)
            
            if not self.results:
                print(f"No data scraped from {self.source_name}. Page structure may have changed.")
                return None
            
            # Save
            df = pd.DataFrame(self.results)
            
            if df.empty:
                print(f"No data parsed for {self.source_name}.")
                return None
            
            # Use data date from the 'Data' column if available, otherwise today's date
            if 'Data' in df.columns:
                unique_dates = df['Data'].dropna().unique()
                if len(unique_dates) == 1 and unique_dates[0]:
                    data_date = unique_dates[0]
                else:
                    data_date = datetime.today().strftime('%Y-%m-%d')
            else:
                data_date = datetime.today().strftime('%Y-%m-%d')
            
            filename = f"{self.source_name}_data_{data_date}.xlsx"
            
            filepath = self.save_to_excel(df, filename)
            
            if filepath:
                print(f"✅ Excel file created: {filename}")
            
            return filepath
        
        except Exception as e:
            print(f"Error scraping {self.source_name}: {e}")
            return None
        
        finally:
            self.cleanup_browser()

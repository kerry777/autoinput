"""Core automation engine using Playwright"""

from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from typing import Optional, Dict, Any, List
import logging
from src.core.config import settings
import asyncio

logger = logging.getLogger(__name__)


class AutomationEngine:
    """Main automation engine for web scraping and interaction"""
    
    def __init__(self):
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        
    async def start(self):
        """Initialize Playwright and browser"""
        self.playwright = await async_playwright().start()
        
        # Launch browser based on settings
        if settings.BROWSER.lower() == "firefox":
            self.browser = await self.playwright.firefox.launch(
                headless=settings.HEADLESS
            )
        elif settings.BROWSER.lower() == "webkit":
            self.browser = await self.playwright.webkit.launch(
                headless=settings.HEADLESS
            )
        else:
            self.browser = await self.playwright.chromium.launch(
                headless=settings.HEADLESS
            )
        
        # Create browser context with viewport settings
        self.context = await self.browser.new_context(
            viewport={
                "width": settings.VIEWPORT_WIDTH,
                "height": settings.VIEWPORT_HEIGHT
            }
        )
        
        # Create a new page
        self.page = await self.context.new_page()
        self.page.set_default_timeout(settings.TIMEOUT)
        
        logger.info(f"Automation engine started with {settings.BROWSER}")
        
    async def stop(self):
        """Clean up Playwright resources"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        
        logger.info("Automation engine stopped")
        
    async def navigate(self, url: str) -> None:
        """Navigate to a URL"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.goto(url, wait_until="networkidle")
        logger.info(f"Navigated to {url}")
        
    async def fill_form(self, selectors: Dict[str, str], data: Dict[str, Any]) -> None:
        """Fill form fields based on selectors and data"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        for field_name, selector in selectors.items():
            if field_name in data:
                await self.page.fill(selector, str(data[field_name]))
                logger.debug(f"Filled {field_name} using {selector}")
                
    async def click(self, selector: str) -> None:
        """Click an element"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.click(selector)
        logger.debug(f"Clicked element: {selector}")
        
    async def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> None:
        """Wait for a selector to appear"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.wait_for_selector(
            selector,
            timeout=timeout or settings.TIMEOUT
        )
        
    async def screenshot(self, path: str) -> None:
        """Take a screenshot"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        await self.page.screenshot(path=path)
        logger.info(f"Screenshot saved to {path}")
        
    async def extract_text(self, selector: str) -> str:
        """Extract text from an element"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        element = await self.page.query_selector(selector)
        if element:
            return await element.text_content()
        return ""
    
    async def extract_table(self, selector: str) -> List[List[str]]:
        """Extract table data"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        table_data = []
        rows = await self.page.query_selector_all(f"{selector} tr")
        
        for row in rows:
            cells = await row.query_selector_all("td, th")
            row_data = []
            for cell in cells:
                text = await cell.text_content()
                row_data.append(text.strip() if text else "")
            table_data.append(row_data)
        
        return table_data
    
    async def download_file(self, selector: str, download_path: str) -> str:
        """Handle file download"""
        if not self.page:
            raise RuntimeError("Browser not initialized")
        
        # Start waiting for download
        async with self.page.expect_download() as download_info:
            await self.page.click(selector)
            
        download = await download_info.value
        
        # Save the download
        await download.save_as(download_path)
        logger.info(f"File downloaded to {download_path}")
        
        return download_path
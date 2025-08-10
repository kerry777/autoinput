import asyncio
from core.smart_login import SmartLoginManager
from playwright.async_api import async_playwright

async def run():
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()
        page = await context.new_page()
        
        smart = SmartLoginManager()
        await smart.login('bizmeka', page)
        
        await page.wait_for_timeout(180000)
        await browser.close()

asyncio.run(run())
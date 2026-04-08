const puppeteer = require('puppeteer');
const path = require('path');

(async () => {
    const browser = await puppeteer.launch({
        headless: 'new',
        args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage']
    });
    
    const page = await browser.newPage();
    await page.setViewport({ width: 1200, height: 630 });
    
    const htmlPath = 'file://' + path.resolve('/root/.agent/diagrams/linkedin-today.html');
    await page.goto(htmlPath, { waitUntil: 'networkidle0' });
    
    await page.screenshot({
        path: '/root/.openclaw/workspace/linkedin-today.png',
        fullPage: false
    });
    
    console.log('Screenshot saved to /root/.openclaw/workspace/linkedin-today.png');
    
    await browser.close();
})();

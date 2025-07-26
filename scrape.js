// scrape.js
const fs = require('fs');
const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const ctx = await browser.newContext({
    userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
  });

  const animeList = JSON.parse(fs.readFileSync('anime_list.json', 'utf8'));
  const result = [];

  for (const { title, url: seriesUrl } of animeList) {
    console.log(`🔍 ${title}`);
    const page = await ctx.newPage();

    // 1. Buka halaman SERIES (daftar episode)
    await page.goto(seriesUrl, { waitUntil: 'domcontentloaded' });

    // 2. Ambil semua link episode
    const epLinks = await page.$$eval(
      '#singlepisode .episodelist a',
      as => as.map(a => a.href)
    );

    // 3. Iterasi per episode
    for (const epUrl of epLinks) {
      await page.goto(epUrl, { waitUntil: 'networkidle' });

      // Tunggu sampai iframe benar-benar punya src
      await page.waitForFunction(
        () => document.querySelector('iframe[src]')?.src.startsWith('http'),
        { timeout: 10000 }
      );

      const epTitle = await page.$eval('h1.entry-title', el => el.textContent.trim())
        .catch(() => epUrl.split('/').slice(-2)[0]);

      const embeds = await page.$$eval('iframe[src]', ifs =>
        ifs.map(f => f.src).filter(u => u && u.startsWith('http'))
      );

      result.push({
        anime: title,
        episode: epTitle,
        url: epUrl,
        embeds
      });
    }
    await page.close();
  }

  fs.writeFileSync('episodes.json', JSON.stringify(result, null, 2));
  console.log(`✅ Done, total ${result.length} items`);
  await browser.close();
})();
          

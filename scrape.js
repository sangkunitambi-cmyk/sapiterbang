// scrape.js
const fs = require('fs');
const playwright = require('playwright');

(async () => {
  const browser = await playwright.chromium.launch({ headless: true });
  const ctx = await browser.newContext({ userAgent: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36' });
  const animeList = JSON.parse(fs.readFileSync('anime_list.json', 'utf8'));
  const episodes = [];

  for (const anime of animeList) {
    console.log(`🔍 ${anime.title}`);
    const page = await ctx.newPage();
    await page.goto(anime.url, { waitUntil: 'networkidle' });

    // grab every episode link on the series page
    const links = await page.$$eval('.episodelist a', as =>
      as.map(a => a.href)
    );

    for (const epUrl of links) {
      await page.goto(epUrl, { waitUntil: 'networkidle' });
      const iframes = await page.$$eval('iframe', ifs =>
        ifs.map(f => f.src).filter(u => u)
      );
      episodes.push({
        anime: anime.title,
        episode: epUrl.split('/').slice(-2)[0],
        url: epUrl,
        embeds: iframes
      });
    }
    await page.close();
  }

  fs.writeFileSync('episodes.json', JSON.stringify(episodes, null, 2));
  console.log(`✅ Scraped ${episodes.length} episodes`);
  await browser.close();
})();

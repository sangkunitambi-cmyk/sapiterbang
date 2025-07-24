import scrapy

class AnichinListModeSpider(scrapy.Spider):
    name = "anichin_listmode"
    allowed_domains = ["anichin.cafe"]
    start_urls = ["https://anichin.cafe/seri/list-mode/"]

    def parse(self, response):
        # Selector bisa diubah sesuai struktur HTML terbaru
        for anime in response.css('div.seri-card, div.seri-card-list'):  # Cek class card yang dipakai di list mode
            title = anime.css('a.seri-title::text').get() or anime.css('h2 a::text').get()
            url = anime.css('a.seri-title::attr(href)').get() or anime.css('h2 a::attr(href)').get()
            image = anime.css('img::attr(src)').get()
            status = anime.css('.seri-status::text').get()
            # Tambah data lain sesuai kebutuhan
            yield {
                'title': title.strip() if title else None,
                'url': response.urljoin(url) if url else None,
                'image': image,
                'status': status.strip() if status else None
            }

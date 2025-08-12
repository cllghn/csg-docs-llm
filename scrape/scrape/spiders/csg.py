import scrapy


class CsgSpider(scrapy.Spider):
    name = "csg"
    allowed_domains = ["csgjusticecenter.org"]
    start_urls = ["https://csgjusticecenter.org"]

    def parse(self, response):
        titles = response.css('h1::text').getall()
        body = response.css('body').get()

        
        for title in titles:
            yield {
                'title': title,
                'body': body,
                'url': response.url
            }
        
        # Follow links to other pages
        next_page = response.css('a.next::attr(href)').get()
        if next_page:
            yield response.follow(next_page, self.parse)

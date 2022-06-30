import scrapy

class ItemsSpider(scrapy.Spider):
    name = "items"
    page = None
    
    def __init__(self, name=name, **kwargs):
        super().__init__(name, **kwargs)
        search_term = kwargs.get('search_term')
        search_term = search_term.replace(' ','-')
        self.start_urls = [f'https://lista.mercadolivre.com.br/{search_term}']
        self.page = 0
    
    def get_price(self, item):
        price_fraction = item.css('.price-tag-fraction::text').get()
        price_cents = item.css('.price-tag-cents::text').get()
        return f'{price_fraction},{price_cents}'
    
    def get_installments_price(self, installments_block):
        installment_price_fraction = installments_block.css('.price-tag-fraction::text').get()
        installment_price_cents = installments_block.css('.price-tag-cents::text').get()
        installment_price = f'{installment_price_fraction}'
        if installment_price_cents:
            installment_price = f'{installment_price_fraction},{installment_price_cents}'
        return installment_price

    def get_store_name(self, item):
        official_store = item.css('.ui-search-official-store-label::text').get()
        if official_store:
            official_store_name = official_store.split('por ')[1]
        else:
            official_store_name = ''
        return official_store_name
    
    def get_product_code(self, link):
        try:
            code = f'MLB-{link.split("/MLB-")[1].split("-")[0]}'
        except Exception:
            code = ''
        return code
        
    def parse(self, response, **kwargs):
        item_class = 'ui-search-layout__item'
        items = response.css(f'.{item_class}')
        self.page += 1
        for item in items:
            name = item.css('.ui-search-item__title::text').get()
            price = self.get_price(item)
            installments_block = item.css('.ui-search-installments')
            installments = int(item.css('.ui-search-item__group__element::text').get().replace('x ',''))
            installment_price = self.get_installments_price(installments_block)
            free_shipping = bool(item.css('.ui-search-item__shipping--free::text').get())
            official_store_name = self.get_store_name(item)
            product_link = item.css('.ui-search-link::attr(href)').get()
            image_block = item.css('.ui-search-result__image')
            image_link = image_block.css('.ui-search-result-image__element::attr(data-src)').get()
            link = image_block.css('.ui-search-link::attr(href)').get()
            product_code = self.get_product_code(link)
            yield {
                'nome_produto': name,
                'preço': price,
                'parcelas': installments,
                'valor_parcelado': installment_price,
                'foto': image_link,
                'frete_gratis': free_shipping,
                'nome_loja': official_store_name,
                'link_produto': product_link,
                'codigo_produto': product_code
            }
        
        next_page_block = response.css('.andes-pagination__button--next')
        next_page = next_page_block.css('.andes-pagination__link::attr(href)').get()
        if self.page < 5 and next_page:
            yield scrapy.Request(next_page, callback=self.parse)
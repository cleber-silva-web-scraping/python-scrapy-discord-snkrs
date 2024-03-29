import scrapy,json, time,random
from datetime import datetime
try:
    from crawler.crawler.items import Inserter, Deleter
except:
    from crawler.items import Inserter, Deleter
class NikeCalendarioSpider(scrapy.Spider):
    name = "nike_calendario"
    encontrados = {}  
    def __init__(self, results, proxy_list=None):  
        self.proxy_pool = proxy_list                    
        self.encontrados[self.name] = []      
        [self.add_name(self.name, str(r['id']))  for r in results if r['spider'] == self.name]
        self.first_time = len(self.encontrados[self.name])

    def make_request(self, url, cb, meta=None, handle_failure=None):
        request = scrapy.Request(dont_filter=True, url =url, callback=cb, meta=meta, errback=handle_failure)
        if self.proxy_pool:
            request.meta['proxy'] = random.choice(self.proxy_pool)              
            self.log('Using proxy {}'.format(request.meta['proxy']))
            self.log('----------------')          
        return request 

    def detail_failure(self, failure):        
        record = Inserter()
        record = failure.request.meta['record']
        # try with a new proxy
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        self.log('Erro em detalhes url {}'.format(failure.request.url))
        request = self.make_request(failure.request.url, self.details, dict(record=record), self.detail_failure)
        yield request 

    def page_failure(self, failure):        
        # try with a new proxy
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))
        self.log('**** Erro em PAGINACAO url {}'.format(failure.request.url))

        request = self.make_request(failure.request.url, self.parse, None, self.page_failure)
        yield request

    def start_requests(self):       
        urls = [
            'https://www.nike.com.br/Snkrs/Calendario?demanda=true&p=1',
        ]
        for url in urls:
            request = self.make_request(url, self.parse, None, self.page_failure)            
            yield request 
            #yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)  
       
    def add_name(self, key, id):
        if key in  self.encontrados:
            self.encontrados[key].append(id)
        else:
            self.encontrados[key] = [id]

    def parse(self, response):     
        finish  = True
        tab = response.url.replace('?','/').split('/')[4]  
        categoria = 'nike_calendario_snkrs'
        
        send = 'avisar' if int(self.first_time) > 0 else 'avisado'

        #pega todos os ites da pagina, apenas os nomes dos tenis
        nodes = [ name for name in response.xpath('//div[contains(@class,"produto produto--")]') ]
        if(len(nodes) > 0 ):
            finish=False
       
        #checa se o que esta na pagina ainda nao esta no banco, nesse caso insere com o status de avisar
        for item in nodes:
            name = item.xpath('.//h2/text()').get()            
            prod_url = item.xpath('.//a/@href').get()
            id = 'ID{}-{}$'.format(item.xpath('.//a/img/@alt').get().split(".")[-1].strip(), tab)            
            imagem = item.xpath('.//div[@class="produto__imagem"]//a//img/@data-src').get()
            release_full = item.xpath('.//h2[@class="produto__detalhe-titulo"]//span[descendant-or-self::text()]').get()
            quando = release_full.replace('<span class="snkr-release__mobile-date">','').replace('<span>','').replace('</span>','') .replace('Disponível às', 'Disponível em')
            deleter = Deleter()                      
            deleter['id']=id
            yield deleter
            record = Inserter()
            record['id']=id
            record['created_at']=datetime.now().strftime('%Y-%m-%d %H:%M') 
            record['spider']=self.name 
            record['codigo']='' 
            record['prod_url']=prod_url 
            record['name']=name 
            record['categoria']=categoria 
            record['tab']=tab 
            record['imagens']=imagem
            record['tamanhos']=json.dumps([{"aguardando": quando}]) 
            record['send']=send    
            record['price']=''   
            record['outros']=''                
            if len( [id_db for id_db in self.encontrados[self.name] if str(id_db) == str(id)]) == 0:     
                self.add_name(self.name, str(id)) 
                yield record  
        
        if(finish == False):
            uri = response.url.split('&p=')
            part = uri[0]
            page = int(uri[1]) + 1
            url = '{}&p={}'.format(part, str(page))
            time.sleep(3)
            request = self.make_request(url, self.parse)            
            yield request 
            #yield scrapy.Request(dont_filter=True, url =url, callback=self.parse)
         
        

      
        


        
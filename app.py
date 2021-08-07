import discord
import scrapy
import os
import time
import scrapy.crawler as crawler
import sqlite3
from multiprocessing import Process, Queue
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging


from crawler.crawler.spiders.nike_snkrs_spider import NikeSnkrsSpider
from crawler.crawler.spiders.nike_calendario_spider import NikeCalendarioSpider
from crawler.crawler.spiders.nike_novidades_spider import NikeNovidadesSpider

from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider
from crawler.crawler.spiders.maze_novidades_spider import MazeNovidadesSpider

from crawler.crawler.spiders.gdlp_snkrs_spider import GdlpSnkrsSpider
from crawler.crawler.spiders.gdlp_novidades_spider import GdlpNovidadesSpider
   
from crawler.crawler.spiders.artwalk_snkrs_spider import ArtwalkSnkrsSpider
from crawler.crawler.spiders.artwalk_calendario_spider import ArtwalkCalendarioSpider
from crawler.crawler.spiders.artwalk_novidades_spider import ArtwalkNovidadesSpider

from crawler.crawler.spiders.magicfeet_snkrs_spider import MagicfeetSnkrsSpider





from discord.ext import tasks


print("app.py")
print(os.path.abspath(os.path.dirname(__file__)))
db_path = '{}/data/nike_database.db'.format(os.path.abspath(os.path.dirname(__file__)).split('crawler/crawler')[0])
print(db_path)

database = sqlite3.connect(db_path)
cursor = database.cursor()




async def run_spider(spider):
    def f(q):
        try:
            configure_logging()
            runner = crawler.CrawlerRunner()
            runner.crawl(spider)            
            deferred = runner.join()
            deferred.addBoth(lambda _: reactor.stop())
            reactor.run()
            q.put(None)
        except Exception as e:
            q.put(e)

    q = Queue()
    p = Process(target=f, args=(q,))
    p.start()
    result = q.get()
    p.join()

    if result is not None:
        raise result


class MyClient(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)


        # start the task to run in the background
        self.my_background_task.start()
        self.checa_database()

    def checa_database(self):
        try:            
            rows = [row[0] for row in cursor.execute('SELECT count(id) FROM products')][0]           
            if int(rows) > 0:
                self.created = True
            else:
                self.created = False                
        except:
            self.created = False


    async def on_ready(self):
        print('Logado...')
        print('Primeira vez. ',self.created)


    @tasks.loop(seconds=600) # task runs every 15 seconds
    async def my_background_task(self):    
        spiders = [
            NikeSnkrsSpider,
            NikeCalendarioSpider,
            NikeNovidadesSpider,
            MazeSnkrsSpider,
            MazeNovidadesSpider,
            GdlpSnkrsSpider,
            GdlpNovidadesSpider,
            ArtwalkSnkrsSpider,
            ArtwalkCalendarioSpider,
            ArtwalkNovidadesSpider,
            MagicfeetSnkrsSpider,
        ]    
        
        channels = [
            # {
            # 'spider': 'nike_snkrs',
            # 'id': 873217111659532288,
            # 'categoria':'restock',            
            # 'mensagem' : 'Novo produto inserido no restock'                
            # },
            # {
            # 'spider': 'nike_novidades',
            # 'id': 873217865686323260,
            # 'categoria':'nov-calcados',            
            # 'mensagem' : 'Novo produto inserido em novidade calçados'                
            # },
            # {
            # 'spider': 'nike_novidades',
            # 'id': 873217679811559534,
            # 'categoria':'nov-acessorios',            
            # 'mensagem' : 'Novo produto inserido em acessórios'                
            # },
            # {
            # 'spider': 'nike_novidades',
            # 'id': 873217679811559534,
            # 'categoria':'nov-roupas',            
            # 'mensagem' : 'Novo produto inserido em roupas'                
            # },

            {
            'spider': 'nike_novidades',
            'id': 873450794404425779,
            'categoria':'nov-roupas',            
            'mensagem' : 'Novo produto generico'                
            }    


                    
        ]

        spiders = [
            'artwalk_calendario',
            'artwalk_novidades',
            'artwalk_snkrs',
            'gdlp_novidades',
            'gdlp_snkrs',
            'magicfeet_snkrs',
            'maze_novidades',
            'maze_snkrs',
            'nike_calendario',
            'nike_novidades',
            'nike_snkrs',
        ]

        tic = time.clock()
        for spider in spiders:
            await run_spider(spider)

            if self.created == False:
                cursor.execute("update products set send='avisado'")
                database.commit()  

            if self.created:           
                for spider in spiders:
                    send_to = self.get_channel(873450794404425779)
                    query = 'SELECT name, url, id FROM products where send="avisar" and spider="{}"'.format(spider)

                    rows = [[str(row[0]).strip(),str(row[1]).strip(), str(row[2]).strip()]  for row in cursor.execute(query)]            
                    for row in rows:
                        print('Enviando mensagem para channel generico')
                        await send_to.send("{}:\n {}\n{}".format('Novo produto generico' , row[0], row[1]))                        
                        cursor.execute("update products set send='avisado' where id='"+row[2]+"'")
                        database.commit()               

            # if self.created:           
            #     for channel in channels:
            #         send_to = self.get_channel(channel['id'])
            #         query = 'SELECT name, url, id FROM products where send="avisar" and spider="{}" and categoria="{}"'.format(channel['spider'],channel['categoria'])

            #         rows = [[str(row[0]).strip(),str(row[1]).strip(), str(row[2]).strip()]  for row in cursor.execute(query)]            
            #         for row in rows:
            #             print('Enviando mensagem para channel {}'.format(channel['id']))
            #             await send_to.send("{}:\n {}\n{}".format(channel['mensagem'], row[0], row[1]))                        
            #             cursor.execute("update products set send='avisado' where id='"+row[2]+"'")
            #             database.commit()
        toc = time.clock()
        now = toc - tic
        print("")
        print('================================================================')
        print('{}s'.format(now))
        print("")
        print("")
        print("")
        self.created = True
        
        

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in

client = MyClient()

client.run('ODcyMTMxNjcwMTcyNjQzMzkw.YQlZ6Q.jFepmzwgmN4iFy-nh5p0qX_gQJU')

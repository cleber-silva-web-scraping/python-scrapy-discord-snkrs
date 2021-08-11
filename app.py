import discord
import scrapy
import json
import os
from multiprocessing import Process, Queue
from twisted.internet import reactor
from scrapy.crawler import CrawlerRunner
from scrapy.utils.log import configure_logging
from crawler.data.database import Database
from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider

from crawler.crawler.spiders.artwalk_calendario_spider import ArtwalkCalendarioSpider
from crawler.crawler.spiders.artwalk_novidades_spider import ArtwalkNovidadesSpider
from crawler.crawler.spiders.artwalk_restock_spider import ArtwalkRestockSpider
from crawler.crawler.spiders.gdlp_novidades_spider import GdlpNovidadesSpider
from crawler.crawler.spiders.gdlp_restock_spider import GdlpRestockSpider
from crawler.crawler.spiders.magicfeet_novidades_spider import MagicfeetNovidadesSpider
from crawler.crawler.spiders.magicfeet_snkrs_spider import MagicfeetSnkrsSpider
from crawler.crawler.spiders.maze_novidades_spider import MazeNovidadesSpider
from crawler.crawler.spiders.maze_restock_spider import MazeRestockSpider
from crawler.crawler.spiders.maze_snkrs_spider import MazeSnkrsSpider
from crawler.crawler.spiders.nike_calendario_spider import NikeCalendarioSpider
from crawler.crawler.spiders.nike_novidades_spider import NikeNovidadesSpider
from crawler.crawler.spiders.nike_restock_spider import NikeRestockSpider


from crawler.crawler import runner_settings as my_settings 
from discord.ext import tasks
from scrapy.settings import Settings


async def run_spider(spider, database):
    def f(q):
        try:
            crawler_settings = Settings()
            configure_logging()
            crawler_settings.setmodule(my_settings)                       
            runner = CrawlerRunner(settings=crawler_settings)
            runner.crawl(spider, database=database)            
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
    def __init__(self, channels=None, *args, **kwargs,):
        super().__init__(*args, **kwargs)        
        # start the task to run in the background
        self.my_background_task.start()       
        self.database = Database()
        self.first_time = self.database.isEmpty()
        try:
            self.channels = channels if channels != None else json.loads(self.database.get_config().replace("'",'"'))
        except:
            self.channels = {}

    async def show_channels(self, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        pretty_dict_str = json.dumps(self.channels, indent=2, sort_keys=True)                        
        await send_to.send(pretty_dict_str)
        return 

    async def delete_by_url(self, url, adm_channel):
        send_to = self.get_channel(int(adm_channel))        
        try:
            url = url.replace('>delete','').strip()
            self.database.delete_by_url(url)            
            await send_to.send("Dados removidos com sucesso!")            
        except Exception as e:                        
            await send_to.send("Erro ao remover os dados! Nada foi perdido.")
        return 
    
    async def set_channels(self, channels, adm_channel):
        send_to = self.get_channel(int(adm_channel))
        bk_channels = self.channels
        try:
            config = channels.replace('>configurar','')            
            channels_temp = json.loads(config)
            self.channels = json.loads(self.database.set_config(channels_temp).replace("'",'"'))            
            await send_to.send("Dados atualizados com sucesso!")            
        except:
            self.channels = json.loads(self.database.set_config(bk_channels).replace("'",'"'))
            await send_to.send("Erro ao atualizar os dados! Nada foi perdido.")
        return 

    async def on_message(self, message):         
        adm_channel = os.environ.get('ADMIN_CHANNEL')
        if adm_channel == None:
            return

        if int(message.channel.id) != int(adm_channel):
            #leave
            return        

        if message.content.startswith('>canais'):
            await self.show_channels(int(adm_channel))
        
        if message.content.startswith('>configurar'):
           await self.set_channels(message.content, int(adm_channel))

        if message.content.startswith('>delete'):
           await self.delete_by_url(message.content, int(adm_channel))
        return

        
    async def on_ready(self):
        print('Logado...')
    
    @tasks.loop(seconds=600) # task runs every 15 seconds
    async def my_background_task(self):        
        spiders = [
            MazeSnkrsSpider,
            # ArtwalkCalendarioSpider,
            # ArtwalkNovidadesSpider,
            # NikeNovidadesSpider,
            # ArtwalkRestockSpider,
            # GdlpNovidadesSpider,
            # GdlpRestockSpider,
            # NikeCalendarioSpider,
            # MagicfeetNovidadesSpider,
            # MagicfeetSnkrsSpider,
            # MazeNovidadesSpider,
            # MazeRestockSpider,
            # MazeSnkrsSpider,
            # NikeRestockSpider,
        ]   

        
        for spider in spiders:         
            await run_spider(spider, self.database)
            if self.first_time:
               self.database.avisar_todos()           
            
            for channel in self.channels:
                channel_id = int(self.channels[channel]['canal'])
                
                send_to = self.get_channel(channel_id)                
                rows = self.database.avisos(channel)                                
                for row in rows:
                    message = '{}'.format(row['name'])
                    embed = discord.Embed(title=message, url=row['url'], color=3066993) #,color=Hex code        
                    embed.set_thumbnail(url=row['imagens'][0])                    
                    content = '\n'.join(row['tamanhos'])
                    titulo = 'Data' if 'Disponível em' in content else 'Tamanhos'
                    embed.add_field(name=titulo, value=content)                    
                    await send_to.send(embed=embed)  
                    self.database.avisado(row['id'])        
        
        self.created = True
        
        

    @my_background_task.before_loop
    async def before_my_task(self):
        await self.wait_until_ready() # wait until the bot logs in


if __name__ == '__main__':    
    key = os.environ.get('DISCORD_SERVER_KEY')
    if key:
        client = MyClient()
        client.run(key)
    else:
        import config_local as config        
        client = MyClient()
        client.run(config.key)

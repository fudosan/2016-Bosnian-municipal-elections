import scrapy
from scrapy.selector import Selector
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import time
import re


def create_driver():
    """Creates a simple webdriver with basic options

    :return: webdriver with configured options
    """
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_path = "path to your chrome driver"
    return webdriver.Chrome(executable_path=chrome_path, options=chrome_options)


class MayorSpider(scrapy.Spider):
    name = 'mayor'
    allowed_domains = ['www.izbori.ba']
    start_urls = ['https://www.izbori.ba/rezultati_izbora_2016/?resId=13&langId=1#/8/0/0']

    def __init__(self):
        driver = create_driver()
        driver.get("https://www.izbori.ba/rezultati_izbora_2016/?resId=13&langId=1#/8/0/0")
        time.sleep(3)
        self.html = driver.page_source
        driver.close()

    def parse(self, response):
        resp = Selector(text=self.html)
        for izborna_jedinica in resp.xpath("//div[@id='leftBar']/div[3]/select/option"):
            izborna_jedinica_name = izborna_jedinica.xpath(".//text()").get()
            if izborna_jedinica_name == '-':
                continue
            izborna_jedinica_value = int(re.search(r'\((\b\d+\b)\)', izborna_jedinica_name).group(1))
            driver = create_driver()
            driver.get(f"https://www.izbori.ba/rezultati_izbora_2016/?resId=13&langId=1#/8/{izborna_jedinica_value}/0")
            time.sleep(2)
            new_page = driver.page_source
            new_page_selectable = Selector(text=new_page)
            options = new_page_selectable.xpath("//div[@id='leftBar']/div[5]/select/option")
            for ind, option in enumerate(options):
                biracko_mjesto = option.xpath('.//text()').get()
                if biracko_mjesto == '-':
                    kandidat_dict = {}
                    broj_obradjenih_listica = new_page_selectable.xpath("//div[@id='leftBar']/span/text()").get().split(':')[-1]
                    broj_vazecih_listica = new_page_selectable.xpath("//div[@id='leftBar']/div[6]/div/span/text()").get().split(':')[-1]
                    broj_vazecih_redovnih_listica = new_page_selectable.xpath("//div[@id='leftBar']/div[6]/div/div[1]/span/span/text()").get()
                    broj_vazecih_posta_listica = new_page_selectable.xpath("//div[@id='leftBar']/div[6]/div/div[2]/span/span/text()").get()
                    broj_vazecih_odsustvo_mobilni_tim_i_DKP_listica = new_page_selectable.xpath("//div[@id='leftBar']/div[6]/div/div[3]/span/span/text()").get()
                    broj_vazecih_potvrdjenih_listica = new_page_selectable.xpath("//div[@id='leftBar']/div[6]/div/div[4]/span/span/text()").get()
                    broj_kandidata = new_page_selectable.xpath("//tr[@class='data']/td[3]/text()").get()
                    for ind, kandidat in enumerate(new_page_selectable.xpath("//div[@class='tableDiv']/table/tbody/tr[@class='ng-scope']")):
                        kandidat_kod = kandidat.xpath(".//td[1]/text()").get()
                        kandidat_mandat = kandidat.xpath(".//td[9]/i").get()
                        if kandidat_mandat is not None:
                            kandidat_mandat = True
                        else:
                            kandidat_mandat = False
                        kandidat_dict[kandidat_kod] = {
                            'broj glasova - biracko mjesto': kandidat.xpath(".//td[3]/text()").get(),
                            'ukupan broj vazecih listica (redovni) - biracko mjesto': kandidat.xpath(".//td[4]/text()").get(),
                            'ukupan broj vazecih listica (posta) - biracko mjesto': kandidat.xpath(".//td[5]/text()").get(),
                            'ukupan broj vazecih listica (odsustvo, mobilni tim i DKP) - biracko mjesto': kandidat.xpath(".//td[6]/text()").get(),
                            'ukupan broj vazecih listica (potvrdjeni) - biracko mjesto': kandidat.xpath(".//td[7]/text()").get(),
                            'mandat': kandidat_mandat
                        }
                    continue
                driver.find_element_by_xpath(f"//div[@id='leftBar']/div[5]/select/option[{ind+1}]").click()
                time.sleep(2)
                new_page_data = driver.page_source
                new_page_selectable_data = Selector(text=new_page_data)
                broj_biraca = new_page_selectable_data.xpath("//tr[@class='data']/td[1]/text()").get()
                broj_izaslih = new_page_selectable_data.xpath("//div[@class='tableDiv']/div[2]/div[1]/div/table/tbody/tr[1]/td[2]/b/text()").get()
                broj_neizaslih = new_page_selectable_data.xpath("//div[@class='tableDiv']/div[2]/div[1]/div/table/tbody/tr[3]/td[2]/b/text()").get()
                broj_vazecih_listica_bir_mjesto = new_page_selectable_data.xpath("//div[@class='tableDiv']/div[2]/div[2]/div/table/tbody/tr[1]/td[2]/b/text()").get()
                broj_nevazecih_praznih_listica = new_page_selectable_data.xpath("//div[@class='tableDiv']/div[2]/div[2]/div/table/tbody/tr[3]/td[2]/b/text()").get()
                broj_nevazecih_listica_drugi_krit = new_page_selectable_data.xpath("//div[@class='tableDiv']/div[2]/div[2]/div/table/tbody/tr[5]/td[2]/b/text()").get()
                for kandidat in new_page_selectable_data.xpath("//div[@class='tableDiv']/table/tbody/tr[@class='ng-scope']"):
                    kandidat_sifra = kandidat.xpath(".//td[1]/text()").get()
                    kandidat_ime = kandidat.xpath(".//td[2]/text()").get()
                    kandidat_broj_glasova = kandidat.xpath(".//td[3]/text()").get()
                    kandidat_broj_glasova_procenti = kandidat.xpath(".//td[4]/text()").get()
                    yield {
                        'izborna jedinica': izborna_jedinica_name,
                        'biracko mjesto': biracko_mjesto,
                        'broj biraca - biracko mjesto': broj_biraca,
                        'broj kandidata': broj_kandidata,
                        'kandidat sifra': kandidat_sifra,
                        'ime i stranka kandidata': kandidat_ime,
                        'broj glasova kandidata - biracko mjesto': kandidat_broj_glasova,
                        'broj glasova kandidata (procenti) - biracko mjesto': kandidat_broj_glasova_procenti,
                        'izasli na izbore - biracko mjesto': broj_izaslih,
                        'nisu izasli na izbore - biracko mjesto': broj_neizaslih,
                        'broj vazecih listica - biracko mjesto': broj_vazecih_listica_bir_mjesto,
                        'broj nevazecih praznih listica - biracko mjesto': broj_nevazecih_praznih_listica,
                        'broj nevazecih praznih listica po drugim kriterijama - biracko mjesto': broj_nevazecih_listica_drugi_krit,
                        'ukupan broj obradjenih listica - izborna jedinica': broj_obradjenih_listica,
                        'ukupan broj vazecih listica - izborna jedinica': broj_vazecih_listica,
                        'ukupan broj vazecih listica (redovni) - izborna jedinica': broj_vazecih_redovnih_listica,
                        'ukupan broj vazecih listica (posta) - izborna jedinica': broj_vazecih_posta_listica,
                        'ukupan broj vazecih listica (odsustvo, mobilni tim i DKP) - izborna jedinica': broj_vazecih_odsustvo_mobilni_tim_i_DKP_listica,
                        'ukupan broj vazecih listica (potvrdjeni) - izborna jedinica': broj_vazecih_potvrdjenih_listica,
                        'broj glasova - biracko mjesto': kandidat_dict[kandidat_sifra]['broj glasova - biracko mjesto'],
                        'ukupan broj vazecih listica (redovni) - biracko mjesto': kandidat_dict[kandidat_sifra]['ukupan broj vazecih listica (redovni) - biracko mjesto'],
                        'ukupan broj vazecih listica (posta) - biracko mjesto': kandidat_dict[kandidat_sifra]['ukupan broj vazecih listica (posta) - biracko mjesto'],
                        'ukupan broj vazecih listica (odsustvo, mobilni tim i DKP) - biracko mjesto': kandidat_dict[kandidat_sifra]['ukupan broj vazecih listica (odsustvo, mobilni tim i DKP) - biracko mjesto'],
                        'ukupan broj vazecih listica (potvrdjeni) - biracko mjesto': kandidat_dict[kandidat_sifra]['ukupan broj vazecih listica (potvrdjeni) - biracko mjesto'],
                        'mandat': kandidat_dict[kandidat_sifra]['mandat']
                    }
            driver.close()
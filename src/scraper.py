# -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 11:00:33 2022

@author: DE001E02544
"""

import requests
import pandas as pd
import time
import logging
import json
import traceback
import re
from selenium.webdriver.common.keys import Keys
from msedge.selenium_tools import Edge
from msedge.selenium_tools import EdgeOptions
from bs4 import BeautifulSoup

class scraper():
    """
    Basic Scraper class.
    """
    
    
    def get_zip_codes(self,rerun):
        """
        Get the zip codes the scraper should scrape.

        Parameters
        ----------
        rerun : int
            Variable to controle if the scraper should use all zip codes or only specific zip codes.

        Returns
        -------
        zip_code_list : list
            List objects with zip codes.

        """
        if rerun == "0":
            zip_code_list = pd.read_csv("../zip_codes_full.csv",encoding="utf-8",dtype ={"ZIP":str})
            return zip_code_list
        else:
            zip_code_list = pd.read_csv("../zip_codes_to_run.csv",encoding="utf-8",dtype ={"ZIP":str})
            return zip_code_list
        
        
        
    def run(self,rerun):
        """
        Run the crawler. First get all zip codes from the input file, then crawl data for all zip codes and store the data in the output folder.

        Returns
        -------
        None.

        """
        zip_code_list = self.get_zip_codes(rerun)
        self.get_data(zip_code_list,rerun)
        
        

class metro_scraper():
    """
    Scraper for metro shops.
    """
    
    
    
    def get_data(self):
        """
        Get the data from the metro website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        ## Creat logger ###
        logger = logging.Logger('Metro')
        fh = logging.FileHandler("../log/metro.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        ## Set browser options ##
        edge_options = EdgeOptions()
        edge_options.use_chromium = True
        edge_options.add_argument('disable-gpu')
        driver = Edge(executable_path="..\webdriver\msedgedriver.exe",options=edge_options)
        driver.maximize_window()
        ## Acces main site ##
        url = "https://www.metro.de/standorte?itm_pm=cookie_consent_accept_button#store-locator_g=50.9080883|6.9396948&store-locator_o=Distance%2CAscending&store-locator_a=50969"
        driver.get(url)
        time.sleep(5)
        ## Find all shops ##
        driver.find_element_by_class_name("store-collapsible-label").click()
        shop_list = driver.find_elements_by_class_name("store-details")
        result_dataset =[]
        for shop in shop_list:
            ## Extract data for each shop ##
            shop_name = shop.find_element_by_class_name("store-name").get_attribute('innerHTML').lower()
            try:
                street = shop.find_element_by_class_name("store-address").get_attribute('innerHTML').lower().split(",")[0]
                zip_code = shop.find_element_by_class_name("store-address").get_attribute('innerHTML').lower().split(",")[1].split(" ")[1]
                city = shop.find_element_by_class_name("store-address").get_attribute('innerHTML').lower().split(",")[1].split(" ")[2]
            except Exception as e: 
                street = 'no data'
                zip_code = 'no data'
                city = 'no data'
            ## Safe data in dataset ##
            result_dataset.append({'name':shop_name,'street':street,'zip_code':zip_code,'city':city})
        ## Export Data to csv ##
        result_frame = pd.DataFrame(result_dataset)
        result_frame.to_csv(path_or_buf='../result/shop_list_metro.csv',index=False,encoding='utf-8')
        #### Close driver ###
        driver.quit()

        

class penny_scraper():
    """
    Scraper for penny shops
    """
    
    
    def get_data(self):
        """
        Get the data from the penny website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        ## Creat logger ### 
        logger = logging.Logger('penny')
        fh = logging.FileHandler("../log/penny.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        ## Acces data from api ##
        url = "https://www.penny.de/.rest/market"
        page = requests.get(url).text
        json_object = json.loads(page)
        result_dataset =[]
        for shop in json_object['results']:
            ## Extract data for each shop ##
            name = shop["marketName"]
            street = shop["street"]
            zip_code = shop["zipCode"]
            city = shop["city"]
            lat = shop["latitude"]
            lon = shop["longitude"]
            result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city,'lat':lat,'lon':lon})
            result_frame = pd.DataFrame(result_dataset)
        ## Export Data to csv ##  
        result_frame.to_csv(path_or_buf='../result/shop_list_penny.csv',index=False,encoding='utf-8')



class netto_scraper(scraper):
    """
    Scraper for netto shops
    """
    
    
    
    def get_data(self,zip_code_list,rerun):
        """
        Get the data from the netto website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        
        ## Creat logger ### 
        logger = logging.Logger('netto')
        fh = logging.FileHandler("../log/netto.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        ## A bit different to get the whole dataset as ones
        if rerun == "0":
            result_id = [] 
            result_dataset = []
        else:
            result_dataset = pd.read_csv("../results/shop_list_netto.csv",sep=',',encoding='utf-8',dtype={"zip_code":str}).to_dict('records')
            result_id = pd.read_csv("../results/shop_list_netto.csv",sep=',',encoding='utf-8')['id'].tolist()
        ## Set browser options ##
        edge_options = EdgeOptions()
        edge_options.use_chromium = True
        edge_options.add_argument('disable-gpu')
        driver = Edge(executable_path="..\webdriver\msedgedriver.exe",options=edge_options)
        driver.maximize_window()
        ## Acces main site ##
        driver.get("https://www.netto-online.de/filialfinder")
        time.sleep(3)
        ## Click cookie button ##
        driver.find_element_by_id("CybotCookiebotDialogBodyLevelButtonLevelOptinAllowAll").click()
        time.sleep(1)
        result_dataset =[]
        for zip_code in zip_code_list["ZIP"]:
            ## Get all shops per zip code ##
            print("Get Data for zip code " + str(zip_code))
            logger.info("Get Data for zip code " + str(zip_code))
            input_field = driver.find_element_by_name("post_code")
            input_field.clear()
            input_field.send_keys(zip_code)
            time.sleep(2)
            input_field.send_keys(Keys.RETURN)
            time.sleep(4)
            shop_list = driver.find_elements_by_class_name("store-item__list")
            
            for shop in shop_list:
                ## Extract data for each shop ##
                try:
                    name = shop.find_element_by_class_name("headline__tertiary--store-normal").get_attribute('innerHTML').lower()
                    adress = shop.find_element_by_class_name("store-finder__inner__box__address").find_elements_by_tag_name("p")[0].get_attribute('innerHTML').lower()
                    street = shop.find_element_by_class_name("store-finder__inner__box__address").find_elements_by_tag_name("p")[1].get_attribute('innerHTML').lower().split(" ")[1]
                    zip_code = shop.find_element_by_class_name("store-finder__inner__box__address").find_elements_by_tag_name("p")[1].get_attribute('innerHTML').lower().split(" ")[0]
                    city = shop.find_element_by_class_name("store-finder__inner__box__address").find_elements_by_tag_name("p")[1].get_attribute('innerHTML').lower().split(" ")[1]
                except Exception as e: 
                    street = 'no data'
                    zip_code = 'no data'
                    city = 'no data'
                    name= 'no data'
                    logger.error("Error getting data from " + str(zip_code))
                    logger.error(traceback.format_exc())
                shop_id = name + "_"+ adress +"_" + street + "_" + str(zip_code)
                if shop_id not in result_id:
                    result_dataset.append({'shop_id':shop_id,'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_frame = pd.DataFrame(result_dataset)
                    result_frame.to_csv(path_or_buf='../result/shop_list_netto.csv',index=False,encoding='utf-8')
                    result_id.append(shop_id)
        ####close driver###
        driver.quit()



class lidl_scraper_old():
    """
    Scraper for lidl shops
    """
    
    
    
    
    def get_sub_urls(self):
        """
        Extract all lists of shops from the webiste

        Returns
        -------
        link_list : list
            DList elements with urls to shop lists.

        """
        page = requests.get("https://www.lidl.de/f/").text
        soup = BeautifulSoup(page, 'html.parser')
        element_list = soup.findAll("div",{'class':'ret-o-store-detail-city'})
        link_list = []
        for element in element_list:
            link_list.append(element.find("a")['href'])
        return link_list
    
    
    def get_data(self):
        """
        Get the data from the lidl website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        link_list = self.get_sub_urls()
        result_dataset = []
        for link in link_list:
            ## Get shop urls ##
            page = requests.get("https://www.lidl.de"+link).text
            soup = BeautifulSoup(page, 'html.parser')
            store_list = soup.find_all("div",{"class":"ret-o-store-detail__address"})
            for store in store_list:
                ## Extract data for each shop ##
                name = "Lidl Filiale"
                street = store.contents[0]
                zip_code = store.contents[2].split(" ")[0]
                city = store.contents[2].split(" ")[1].rstrip()
                result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                result_frame = pd.DataFrame(result_dataset)
                result_frame.to_csv(path_or_buf='../result/shop_list_lidl.csv',index=False,encoding='utf-8')
 
                
 
class handelshof_scraper():
    """
    Scraper for handelshof shops
    """
    
    
    
    def get_data(self):
        """
        Get the data from the handelshof website and safe them as a .csv file. List with links must be defind in data folder.

        Returns
        -------
        None.

        """
        result_list = []
        ## Get links to scrape ##
        link_list = open("../data/handelshof_list.txt", "r")
        urls = link_list.read()
        url_list = urls.split(",")
        link_list.close()
        result_dataset = []
        for url in url_list:
            ## Extract data for each shop ##
            page = requests.get(url).text
            soup = BeautifulSoup(page, 'html.parser')
            card = soup.find("div",{"class":"util-text-center-sm"})
            name = card.find_all("p")[0].find_all("span")[0].decode_contents().lstrip().rstrip().lower()
            street = card.find_all("p")[0].find_all("span")[1].decode_contents().lstrip().rstrip().lower()
            zip_code = card.find_all("p")[0].find_all("span")[2].decode_contents().lstrip().rstrip().lower()
            city = card.find_all("p")[0].find_all("span")[3].decode_contents().lstrip().rstrip().lower()
            result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
            result_frame = pd.DataFrame(result_dataset)
        ## Export Data to csv ##
        result_frame.to_csv(path_or_buf='../result/shop_list_handelshof.csv',index=False,encoding='utf-8')
            
           
            
class kaufland_scraper():
    """
    Scraper for kaufland shops
    """
    
    
    def get_data(self):
        """
        Get the data from the kaufland website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        ## Acces api ##
        url= "https://filiale.kaufland.de/.klstorefinder.json"
        page = requests.get(url).text
        json_array = json.loads(page)
        result_dataset = []
        for shop in json_array:
            ## Extract data for each shop ##
            name = shop["cn"]
            zip_code = shop["pc"]
            street = shop["sn"]
            city = shop["t"]
            lat = shop["lat"]
            lon = shop["lng"]
            result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city,'lat':lat,'lon':lon})
            result_frame = pd.DataFrame(result_dataset)
            ## Export Data to csv ##
            result_frame.to_csv(path_or_buf='../result/shop_list_kaufland.csv',index=False,encoding='utf-8')



class real_scraper():
    """
    Scraper for real shops
    """
    
    
    def get_data(self):
        """
        Get the data from the real website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        ## Get all shop urls ##
        basic_url = "https://www.real-markt.de/rechtliches/marktliste/"
        page = requests.get(basic_url).text
        soup = BeautifulSoup(page, 'html.parser')
        shops_list = soup.find("div",{"id":"mobileResults"}).find_all("li")
        result_dataset = []
        for shop in shops_list:
            ## Extract data for each shop ##
            name = shop.find("strong",{"class":"market_list_name block"}).decode_contents().lstrip().rstrip().lower()
            street = shop.find("p").decode_contents().lstrip().rstrip().lower().split(",")[0]
            zip_code = shop.find("p").decode_contents().lstrip().rstrip().lower().split(",")[0]
            shop_url = shop.find("a")["href"]
            sub_page = requests.get(shop_url).text
            soup_shop = BeautifulSoup(sub_page, 'html.parser')
            lat = soup_shop.find("meta",{"itemprop":"latitude"})["content"]
            lon = soup_shop.find("meta",{"itemprop":"longitude"})["content"]
            result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'lat':lat,'lon':lon})
            result_frame = pd.DataFrame(result_dataset)
            ## Export Data to csv ##
            result_frame.to_csv(path_or_buf='../result/shop_list_real.csv',index=False,encoding='utf-8')
            
 


class edeka_scraper(scraper):
    """
    Scraper for edeka shops
    """
    
    
    def get_data(self,zip_code_list,rerun):
        """
        Get the data from the edeka website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        basic_url = "https://www.edeka.de/api/marketsearch/markets?searchstring="
        i = 0
        result_dataset = []
        result_ids = []
        ## Creat logger ##
        logger = logging.Logger('edeka')
        fh = logging.FileHandler("../log/edeka.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        for zip_code in zip_code_list["ZIP"]:
            i += 1
            print("Zip Code number " + str(i) + " of " + str(len(zip_code_list)))
            try:
                ## Acces data from api ##
                page = requests.get(basic_url + str(zip_code)).text
                json_array = json.loads(page)["markets"]
                for shop in json_array:
                    ## Extract data for each shop ##
                    shop_id = shop["id"]
                    name = shop["name"]
                    street = shop["contact"]["address"]["street"]
                    zip_code = shop["contact"]["address"]["city"]["zipCode"]
                    city = shop["contact"]["address"]["city"]["name"]
                    lat = shop["coordinates"]["lat"]
                    lon = shop["coordinates"]["lon"]
                    if shop_id not in result_ids:
                        result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city,'lat':lat,'lon':lon})
                        result_ids.append(shop_id)
                        result_frame = pd.DataFrame(result_dataset)
                    ## Export Data to csv ##
                    result_frame.to_csv(path_or_buf='../result/shop_list_edeka.csv',index=False,encoding='utf-8')
            except Exception as e:
                logger.error("Error with plz " + str(zip_code))
                logger.error(traceback.format_exc())
                
class hit_scraper(scraper):
    """
    Scraper for hit shops
    """
    
    
    def get_data(self,zip_code_list,rerun):
        """
        Get the data from the hit website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        ## acces api ##
        url = "https://www.hit.de/1.0/api/store/search.json?address=33102"
        result_dataset = []
        result_ids = []
        ## Creat logger ##
        logger = logging.Logger('hit')
        fh = logging.FileHandler("../log/hit.log")
        fh.setLevel(logging.INFO)
        fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
        logger.addHandler(fh)
        try:
            
            page = requests.get(url).text
            json_array = json.loads(page)["list"]
            for shop in json_array:
                ## Extract data for each shop ##
                shop_id = shop["id"]
                name = shop["name"]
                street = shop["street"]
                zip_code = shop["zip"]
                city = shop["city"]
                lat = shop["latitude"]
                lon = shop["longitude"]
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city,'lat':lat,'lon':lon})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_hit.csv',index=False,encoding='utf-8')
        except Exception as e:
            logger.error("Error with plz " + str(zip_code))
            logger.error(traceback.format_exc())
    


class rewe_scraper():
    """
    Scraper for rewe shops
    """
    
    def get_data(self):
        """
        Get the data from the meinprospekt website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        basi_url = "https://www.meinprospekt.de/filialen/rewe-de/"
        result_dataset = []
        result_ids = []
        ## check how manny sites are avalable and change number in code ##
        for i in range(0,10):
            ## Get all shop urls ##
            page = requests.get(basi_url+str(i)).text
            soup = BeautifulSoup(page, 'html.parser')
            shop_list = soup.find_all("li",{"itemtype":"http://schema.org/LocalBusiness"})
            for shop in shop_list:
                ## Extract data for each shop ##
                name = shop.find("strong",{"itemprop":"name"}).decode_contents().lstrip().rstrip().lower()
                street = shop.find("span",{"itemprop":"streetAddress"}).decode_contents().lstrip().rstrip().lower()
                zip_code = shop.find("span",{"itemprop":"postalCode"}).decode_contents().lstrip().rstrip().lower()
                city = shop.find("span",{"itemprop":"addressLocality"}).decode_contents().lstrip().rstrip().lower()
                shop_id = name + street + str(zip_code) + city
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_rewe.csv',index=False,encoding='utf-8')

class netto_Scraper():
    """
    Scraper for netto shops
    """
    
    def get_data(self):
        """
        Get the data from the meinprospekt website and safe them as a .csv file. 

        Returns
        -------
        None.

        """
        basi_url = "https://www.meinprospekt.de/filialen/netto-marken-discount-de/"
        result_dataset = []
        result_ids = []
        ## check how manny sites are avalable and change number in code ##
        for i in range(0,10):
            page = requests.get(basi_url+str(i)).text
            soup = BeautifulSoup(page, 'html.parser')
            shop_list = soup.find_all("li",{"itemtype":"http://schema.org/LocalBusiness"})
            for shop in shop_list:
                ## Extract data for each shop ##
                name = shop.find("strong",{"itemprop":"name"}).decode_contents().lstrip().rstrip().lower()
                street = shop.find("span",{"itemprop":"streetAddress"}).decode_contents().lstrip().rstrip().lower()
                zip_code = shop.find("span",{"itemprop":"postalCode"}).decode_contents().lstrip().rstrip().lower()
                city = shop.find("span",{"itemprop":"addressLocality"}).decode_contents().lstrip().rstrip().lower()
                shop_id = name + street + str(zip_code) + city
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_netto.csv',index=False,encoding='utf-8')
    
class netto_mit_dem_scottie_scraper():
    """
    Scraper for netto shops
    """
    
    
    def get_data(self):
        """
        Get the data from the meinprospekt website and safe them as a .csv file. 

        Returns
        -------
        None.

        """
        basi_url = "https://www.meinprospekt.de/filialen/netto1-de/"
        result_dataset = []
        result_ids = []
        ## check how manny sites are avalable and change number in code ##
        for i in range(0,4):
            page = requests.get(basi_url+str(i)).text
            soup = BeautifulSoup(page, 'html.parser')
            shop_list = soup.find_all("li",{"itemtype":"http://schema.org/LocalBusiness"})
            for shop in shop_list:
                ## Extract data for each shop ##
                name = shop.find("strong",{"itemprop":"name"}).decode_contents().lstrip().rstrip().lower()
                street = shop.find("span",{"itemprop":"streetAddress"}).decode_contents().lstrip().rstrip().lower()
                zip_code = shop.find("span",{"itemprop":"postalCode"}).decode_contents().lstrip().rstrip().lower()
                city = shop.find("span",{"itemprop":"addressLocality"}).decode_contents().lstrip().rstrip().lower()
                shop_id = name + street + str(zip_code) + city
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_netto_1.csv',index=False,encoding='utf-8')
    
    
    
class lidl_scraper():
    """
    Scraper for lidl shops
    """
    
    
    
    def get_data(self):
        """
        Get the data from the meinprospekt website and safe them as a .csv file.
        
        Returns
        -------
        None.

        """
        basi_url = "https://www.meinprospekt.de/filialen/lidl/"
        result_dataset = []
        result_ids = []
        ## check how manny sites are avalable and change number in code ##
        for i in range(0,10):
            page = requests.get(basi_url+str(i)).text
            soup = BeautifulSoup(page, 'html.parser')
            shop_list = soup.find_all("li",{"itemtype":"http://schema.org/LocalBusiness"})
            for shop in shop_list:
                ## Extract data for each shop ##
                name = shop.find("strong",{"itemprop":"name"}).decode_contents().lstrip().rstrip().lower()
                street = shop.find("span",{"itemprop":"streetAddress"}).decode_contents().lstrip().rstrip().lower()
                zip_code = shop.find("span",{"itemprop":"postalCode"}).decode_contents().lstrip().rstrip().lower()
                city = shop.find("span",{"itemprop":"addressLocality"}).decode_contents().lstrip().rstrip().lower()
                shop_id = name + street + str(zip_code) + city
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_lidl_new.csv',index=False,encoding='utf-8')

class aldi_scraper():
    """
    Scraper for aldi shops
    """
    

    def get_data(self):
        """
        Get the data from the meinprospekt website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        basi_url = "https://www.meinprospekt.de/filialen/aldinord-de/"
        result_dataset = []
        result_ids = []
        ## check how manny sites are avalable and change number in code ##
        for i in range(0,10):
            page = requests.get(basi_url+str(i)).text
            soup = BeautifulSoup(page, 'html.parser')
            shop_list = soup.find_all("li",{"itemtype":"http://schema.org/LocalBusiness"})
            for shop in shop_list:
                ## Extract data for each shop ##
                name = shop.find("strong",{"itemprop":"name"}).decode_contents().lstrip().rstrip().lower()
                street = shop.find("span",{"itemprop":"streetAddress"}).decode_contents().lstrip().rstrip().lower()
                zip_code = shop.find("span",{"itemprop":"postalCode"}).decode_contents().lstrip().rstrip().lower()
                city = shop.find("span",{"itemprop":"addressLocality"}).decode_contents().lstrip().rstrip().lower()
                shop_id = name + street + str(zip_code) + city
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_aldi_nord.csv',index=False,encoding='utf-8')
                                
class aldi_sued_scraper():
    """
    Scraper for aldi shops
    """
    
    
    
    def get_data(self):
        """
        Get the data from the meinprospekt website and safe them as a .csv file.

        Returns
        -------
        None.

        """
        basi_url = "https://www.meinprospekt.de/filialen/aldisued-de/"
        result_dataset = []
        result_ids = []
        ## check how manny sites are avalable and change number in code ##
        for i in range(0,10):
            page = requests.get(basi_url+str(i)).text
            soup = BeautifulSoup(page, 'html.parser')
            shop_list = soup.find_all("li",{"itemtype":"http://schema.org/LocalBusiness"})
            for shop in shop_list:
                ## Extract data for each shop ##
                name = shop.find("strong",{"itemprop":"name"}).decode_contents().lstrip().rstrip().lower()
                street = shop.find("span",{"itemprop":"streetAddress"}).decode_contents().lstrip().rstrip().lower()
                zip_code = shop.find("span",{"itemprop":"postalCode"}).decode_contents().lstrip().rstrip().lower()
                city = shop.find("span",{"itemprop":"addressLocality"}).decode_contents().lstrip().rstrip().lower()
                shop_id = name + street + str(zip_code) + city
                if shop_id not in result_ids:
                    result_dataset.append({'name':name,'street':street,'zip_code':zip_code,'city':city})
                    result_ids.append(shop_id)
                    result_frame = pd.DataFrame(result_dataset)
                ## Export Data to csv ##
                result_frame.to_csv(path_or_buf='../result/shop_list_aldi_sued.csv',index=False,encoding='utf-8')


class selgros_scraper():
    """
    Scraper for selgros shops
    """
    
    
    
    def get_data(self):
       """
       Get the data from the selgros website and safe them as a .csv file.

       Returns
       -------
       None.

       """
       basi_url = "https://www.selgros.de/maerkte"
       page = requests.get(basi_url).text
       soup = BeautifulSoup(page , 'html.parser')
       json_soup = soup.find_all("div",{"class":"map"})
       text= ""
       ## Get all objects from website ##
       for element in json_soup:
           text = element.get('data-map-props')
       json_object = json.loads(text)
       result_dataset = []
       
       for obj in json_object["locations"]:
           ## Extract data for each shop ##
           match = re.match("(.*),(.*)", obj["map_location_coordinates"])
           lat = match.group(1)
           lon = match.group(2)
           name = obj["map_location_properties"]["name"]
           result_dataset.append({'name':name,'lat':lat,'lon':lon})
       result_frame = pd.DataFrame(result_dataset)
       ## Export Data to csv ##
       result_frame.to_csv(path_or_buf='../result/shop_list_selgros.csv',index=False,encoding='utf-8')


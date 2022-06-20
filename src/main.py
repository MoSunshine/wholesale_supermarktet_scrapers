# -*- coding: utf-8 -*-
"""
Created on Mon Jan 24 11:00:29 2022

@author: DE001E02544
"""
from scraper import penny_scraper, metro_scraper, netto_scraper, edeka_scraper
import logging
import sys
## Main methode ##
def main(mode,rerun):
    if mode == "1":
        ps = penny_scraper()
        ps.get_data()
    if mode == "2":
        ms = metro_scraper()
        ms.get_data()
    if mode == "3":
        ns = netto_scraper()
        ns.run(rerun)
    if mode == "4":
        es = edeka_scraper()
        es.run(rerun)
    
    
    
    
###Start programm ###
if __name__ == "__main__":
    ## Creat logger ##
    logger = logging.Logger('main logger')
    fh = logging.FileHandler("../log/main.log")
    fh.setLevel(logging.INFO)
    fh.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
    logger.addHandler(fh)
    ## Start programm ##
    try:
        main(sys.argv[1],sys.argv[2])
    except Exception as e:
        logger.error(e)

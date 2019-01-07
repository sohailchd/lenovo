from bs4 import BeautifulSoup
import requests 
import re
from flask import Flask
import json



base_url = "https://www.lenovo.com/us/en/outletus/laptops/c/LAPTOPS?menu-id=Laptops_Ultrabooks"
new_laptops_url = "https://www.lenovo.com/us/en/outletus/laptops/c/LAPTOPS?q=%3Aprice-asc%3AfacetSys-Condition%3ANew&uq=&text="
base_url_with_page = "https://www.lenovo.com/us/en/outletus/laptops/c/LAPTOPS?q=%3Aprice-asc%3AfacetSys-Condition%3ARefurbished&page="

total_refurbished = 0
new_items = 0
numbers_re = re.compile(r"[0-9]+")
items_per_page = 8


class DataManager():

    def __get_total_refurbished_latops_count(self):
        '''
        '''
        home_page_content = requests.get(base_url).content
        soup = BeautifulSoup(home_page_content,"lxml")
        product_condition = soup.find('div',{"id" : "facet-list-item-1"})
        
        product_condition_list = product_condition.find_all('li')
        for i in product_condition_list :
            if "Refurbished" in i.text.strip():
                total_ref =  re.search(r"[0-9]+",i.text.strip())    ##i.text.strip().split(' ')
                total_refurbished = total_ref.group()
                print(f"Total refurbished products found : {total_refurbished}")
        
            if "New" in i.text.strip():
                new_ = re.search(r"[0-9]+",i.text.strip())
                new_items = new_.group()
                print(new_items)

        return int(total_refurbished)


    def __parse_data(self,laptops_containers):
        '''
        '''

        page_laptops = dict()

        if laptops_containers:
            pass 
        
        
        for i in laptops_containers:
                content = i.text.strip().split("\n\n")
                data_list = [i for i in content if i !="" ]    ## remove the empty matches
                print(f"content : {content}")

                counter = 0
                for data in data_list:
                    counter += 1
                    if "Refurbished" in data:
                        name = str(data.strip().split("-")[0])
                        # print(name)
                    if ("List Price" in data) or ("Outlet Price" in data):
                         price = str(data_list[counter].strip().split()[0])
                        #  print(price)

                    ## part.no 
                    if "Part number" in data:
                        part_no = str(data.strip().split(":")[1]).strip()
                        # print(part_no)

                    if "Memory" in data:
                        mem = str(data.strip().split(":")[1]).strip()
                        # print(mem)

                    if "Hard Drive" in data:
                        hdd = str(data.strip().split(":")[1]).strip()
                        # print(hdd)
                   
                        
                page_laptops.update({part_no : 
                {
                    "name": name,
                    "price":price,
                    "mem" : mem,
                    "hdd" : hdd
                }})
                print("------------------------------------------------------")

        # print(page_laptops)
        return page_laptops
        


    def get_all_laptops(self,type="Refurbished"):
        '''
        '''
        tref = self.__get_total_refurbished_latops_count()
        total_pages = int(tref/items_per_page) 

        all_laptops = dict()

        for i in range(total_pages):
            url = base_url_with_page + str(i)
            r = requests.get(url)
            print(f"found page : {i}")
            
            ### results div 
            soup = BeautifulSoup(r.text,"lxml")
            results = soup.find_all('div',id="resultsList")
            ### find all the laptops 
            laptops_containers = results[0].find_all('div',{"class" : "facetedResults-item only-allow-small-pricingSummary"})
            
            try:
                all_laptops.update(self.__parse_data(laptops_containers))
            except Exception as e:
                print(f"error while fetching data at page : {i}, {e}")
                continue

        if all_laptops:
            return all_laptops
        else:
            return False


dmanager = DataManager()


app = Flask(__name__)
@app.route("/")
def get_data():
        received = False 
        if not received:
                received = dmanager.get_all_laptops()

        return json.dumps(received)


if __name__ == "__main__":
        app.run(debug=True)

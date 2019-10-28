from flask import render_template
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
DATA_FILE = 'laptop.json'


class DataManager():

    def __init__(self):
        self.received = False
        self.data = None

    def __get_total_refurbished_latops_count(self):
        '''
        '''
        home_page_content = requests.get(base_url).content
        soup = BeautifulSoup(home_page_content, "lxml")
        product_condition = soup.find('div', {"id": "facet-list-item-1"})

        product_condition_list = product_condition.find_all('li')
        for i in product_condition_list:
            if "Refurbished" in i.text.strip():
                # i.text.strip().split(' ')
                total_ref = re.search(r"[0-9]+", i.text.strip())
                total_refurbished = total_ref.group()
                print(
                    f"Total refurbished products found : {total_refurbished}")

            if "New" in i.text.strip():
                new_ = re.search(r"[0-9]+", i.text.strip())
                new_items = new_.group()
                print(new_items)

        return int(total_refurbished)

    def __parse_data(self, laptops_containers):
        '''
        '''

        page_laptops = dict()

        if laptops_containers:
            pass

        for i in laptops_containers:
            content = i.text.strip().split("\n\n")
            # remove the empty matches
            data_list = [i for i in content if i != ""]
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

                # part.no
                if "Part number" in data:
                    part_no = str(data.strip().split(":")[1]).strip()
                    # print(part_no)

                if "Memory" in data:
                    mem = str(data.strip().split(":")[1]).strip()
                    # print(mem)

                if "Hard Drive" in data:
                    hdd = str(data.strip().split(":")[1]).strip()
                    # print(hdd)

            page_laptops.update({part_no:
                                 {
                                     "name": name,
                                     "price": price,
                                     "mem": mem,
                                     "hdd": hdd
                                 }})
            print("------------------------------------------------------")

        # print(page_laptops)
        return page_laptops

    def get_all_laptops(self, type="Refurbished"):
        '''
        '''
        tref = self.__get_total_refurbished_latops_count()
        total_pages = int(tref/items_per_page)

        all_laptops = dict()

        for i in range(total_pages):
            url = base_url_with_page + str(i)
            r = requests.get(url)
            print(f"found page : {i}")

            # results div
            soup = BeautifulSoup(r.text, "lxml")
            results = soup.find_all('div', id="resultsList")
            # find all the laptops
            laptops_containers = results[0].find_all(
                'div', {"class": "facetedResults-item only-allow-small-pricingSummary"})

            try:
                all_laptops.update(self.__parse_data(laptops_containers))
            except Exception as e:
                print(f"error while fetching data at page : {i}, {e}")
                continue

        if all_laptops:
            self.received = True
            return all_laptops
        else:
            return False

    def fetch_data_from_lenovo_outlet(self, update=False):
        if not self.received:
            if not self.data:
                self.data = self.get_all_laptops()
                self.save_json_file()
        else:
            return self.data

    def save_json_file(self, data=None, update=False):
        with open(DATA_FILE, 'w') as jfile:
            if self.data and not data:
                json.dump(self.data, jfile)
            else:
                json.dump(data, jfile)

    def get_table_data(self):
        '''
            reads the json file and returns if the it is not empty
            idea is if there is file we can use it to show the data and in 
            background we can update the data
        '''
        data = []
        records = 0
        jsondata = {
            "draw": 1,
            "recordsTotal": 0,
            "recordsFiltered": 0,
            "data": []
        }
        try:
            with open(DATA_FILE, 'r') as jfile:
                laptops = json.load(jfile)
                for i in laptops:
                    records += 1
                    t = []
                    for j in laptops[i]:
                        t.append(laptops[i][j])
                    data.append(t)

            jsondata['recordsTotal'] = records
            jsondata['recordsFiltered'] = records
            jsondata['data'] = data
            return jsondata
        except Exception as e:
            print(e)
            return None


dmanager = DataManager()
# dmanager.get_table_data()


app = Flask(__name__)


@app.route("/")
def hello():
    return render_template('index.html')


@app.route("/data")
def get_data():
    return json.dumps(dmanager.get_table_data())


@app.route("/update")
def update_data():
    return json.dumps(dmanager.fetch_data_from_lenovo_outlet(update=True))


if __name__ == "__main__":
    app.run(debug=True)

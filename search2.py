import requests
import time
import csv
import os
from pprint import pprint
from parsel import Selector

# implementing the search for the site from website

def certs_at_postcode(postcode):
    """
    Search for certificates at a specific postcode.
    """
    url = ("https://find-energy-certificate.service.gov.uk/" +
           "find-a-non-domestic-certificate/search-by-postcode?" +
           f"postcode={postcode}")
    sesh = requests.Session()
    sesh.headers.update({'User-Agent': 'Mozilla/5.0'})
    data = sesh.get(url).content
    return extract_certs(data)


def extract_certs(html_data):
    """
    Extract the list of certificates from some page data.

    Return a list of dicts:
        [
            {"address": "first line of address",
             "certificate_type": "CEPC",
             "certificate_id": "9934-2085-0318-0600-7601",
             "valid_until": "4 July 2030"},
            {"address": ...}
        ]
    """

    all_certs = []

    selector = Selector(text=html_data.decode())

    table = selector.css("tbody")

    rows = table.css("th,td")  # some rows don't have css tags

    cert = {}

    for row in rows:

        if row.css("th"):
            address = row.css("th::text").get().strip()

        elif row.css("a"):
            cert_id = row.xpath("a/@href").get().split("/")[-1]            
            cert_type = row.css("a::text").get().strip()

        else:
            cert_date = row.css("span::text").get().strip()
            cert = {"address": address, "certificate_type": cert_type, "certificate_id": cert_id, "valid_until": cert_date}
            all_certs.append(cert)
    #print(all_certs)
    return all_certs


def certs_of_type(cert_list):

    result = []
    for i in range(len(cert_list)):
        i = 0
        if cert_list[i]['certificate_type'] != 'AC-CERT':
            del cert_list[i]
        else:
            result.append(cert_list[i]) 
            del cert_list[i]
    return result


def create_new_url(cert):
    print(cert)
    url = "https://find-energy-certificate.service.gov.uk/energy-certificate/"+str(cert["certificate_id"])
    print(url)
    return url


# scraping data from report found

def certs_at_site(url):
    data = requests.get(url).content
    return extract_data(data)


def extract_data(html_data):

    try:
        selector2 = Selector(text=html_data.decode())
        selector3 = Selector(text=html_data.decode())
        subsystems_section1 = selector2.css("div#assessment_details")
        subsystems_section2 = selector3.css("div#assessor_details")
        all_tables1 = subsystems_section1.css("dl.govuk-summary-list")
        all_tables2 = subsystems_section2.css("dl.govuk-summary-list")
        tempDictx = {}
        tempDicty = {}
        all_results = {}

        for table in all_tables1:
            tempDictx.update(extract_assessment(table))

        for table in all_tables2:
            tempDicty.update(extract_assessor(table))

        all_results.update(merge_two_dicts(tempDictx,tempDicty))

        print(all_results)
        return all_results
    except:
        print("failed to extract")
    try:
        selector2 = Selector(text=html_data.encode().decode())
        selector3 = Selector(text=html_data.encode().decode())
        subsystems_section1 = selector2.css("div#assessment_details")
        subsystems_section2 = selector3.css("div#assessor_details")
        all_tables1 = subsystems_section1.css("dl.govuk-summary-list")
        all_tables2 = subsystems_section2.css("dl.govuk-summary-list")
        tempDictx = {}
        tempDicty = {}
        all_results = {}

        for table in all_tables1:
            tempDictx.update(extract_assessment(table))

        for table in all_tables2:
            tempDicty.update(extract_assessor(table))

        all_results.update(merge_two_dicts(tempDictx,tempDicty))

        print(all_results)
        return all_results
    except:
        print("failed to extract")

def merge_two_dicts(x, y):
    z = x.copy()   # start with keys and values of x
    z.update(y)    # modifies z with keys and values of y
    return z

def extract_assessment(table):
    assessment = {}
    rows = table.css("div.govuk-summary-list__row")
    for row in rows:
        key = row.css("dt.govuk-summary-list__key::text").get().strip()
        value = row.css("dd.govuk-summary-list__value::text").get().strip()
        if key in ("Inspection date","Total effective rated output","Treated floor area"):
            assessment[key] = value
    return assessment

def extract_assessor(table):
    assessor = {}
    rows = table.css("div.govuk-summary-list__row")
    for row in rows:
        key = row.css("dt.govuk-summary-list__key::text").get().strip()
        value = row.css("dd.govuk-summary-list__value::text").get().strip()
        if key in ("Assessor’s name","Employer/Trading name"):
            assessor[key] = value
    return assessor

#def extract_subsystem(table):
    subsystem = {}
    rows = table.css("div.govuk-summary-list__row")
    for row in rows:
        key = row.css("dt.govuk-summary-list__key::text").get().strip()
        value = row.css("dd.govuk-summary-list__value::text").get().strip()
        if key in ("Rated Cooling Capacity (kW)", "Description (type/details)", "Manufacturer", "Model/Reference", "Refrigerant Charge (kg)", "Refrigerant Type", "Serial Number", "Year Plant Installed"):
            subsystem[key] = value
    return subsystem

def format_output(final_data, postcode, address):
    field_names = ["Assessor’s name", "Employer/Trading name","Address", "Postcode","Inspection date", "Total effective rated output", "Treated floor area"]
    row = {"Postcode": postcode, "Address": address}
    final_data.update(row)
    print(address)
    with open('Manchester.csv', 'a', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=field_names)
        writer.writeheader()
        writer.writerow(final_data)

def download_file(url):

        if not os.path.exists("cache"):
            os.mkdir("cache")
        file_path = os.path.join("cache", url)
        txt_file_path = file_path
        char_to_replace = {"\\": "_", "//": "_", ".": "_", ":": "_", "/": "_"}
        for key, value in char_to_replace.items():
            txt_file_path = txt_file_path.replace(key, value)

        if not os.path.exists(txt_file_path):
            data = requests.get(url).content  # or however this goes
            with open(txt_file_path, "wb") as fout:
                fout.write(data)
            return data

        else:
            with open(txt_file_path, "r", encoding='utf-8') as fin:
                return fin.read()

def main():

    fileList = []
    basepath = 'TestLists/'

    for entry in os.listdir(basepath):
        if os.path.isfile(os.path.join(basepath, entry)):
            fileList.append(entry)

    for entry in fileList:
        print(entry)
        file = open(basepath+entry, "r")
        csv_reader = csv.reader(file)
        list_from_csv = list(csv_reader)
        final_list = list_from_csv[0]
        print(final_list)

        for i in final_list:
            time.sleep(2.1)
            i=i.replace("ï»¿", "")
            print(i)
            try:
                cert = certs_of_type(certs_at_postcode(i))
            except:
                continue
            for j in cert:
                time.sleep(2.1)
                url = create_new_url(j)
                a = j["address"]
                format_output(extract_data(download_file(url)), i,a)
        
if __name__ == "__main__":
    main()
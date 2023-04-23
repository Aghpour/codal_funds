import requests
import urllib.parse
import json
import re
import logging
from pathlib import Path
import os
from IPython.display import clear_output
import glob

logging.basicConfig(level=logging.INFO)

symbols = ['آگاس', 'کاردان']
headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"}
download_failed = []
main_dir = str(Path.home() / "Downloads")
links0 = {}
def convert(symbol):
    """
    Convert symbol text to hex
    :param ticker: The ticker to search for
    :return: converted text
    """
    parts = symbol.split()
    if len(parts) > 1:
        conveterted_parts = [urllib.parse.quote(part, encoding='utf-8') for part in parts]
        s = '+'.join(conveterted_parts)
        return s
    else:
        s = urllib.parse.quote(symbol, encoding='utf-8')
        return s

def make_dir(symbol):
    """
    Create a directory for a given ticker
    :param ticker: The ticker to search for
    :return: ''
    """
    os.chdir(main_dir)
    ticker_dir = f'{main_dir}\Codal\{symbol}'
    os.makedirs(ticker_dir, exist_ok=True)
    os.chdir(ticker_dir)
    logging.info(f'Directory "{ticker_dir}" created for "{symbol}"')
    return ticker_dir

def file_counter(ticker_dir):
    """
    Count number of files in a directory
    :param ticker_dir: Directory of a symbol
    :return: number of files
    """
    file_count = len(glob.glob(ticker_dir+"/*"))
    return file_count

def get_pages_count(symbol, converted_symbol):
    """
    Get the number of pages for a given ticker
    :param ticker: The ticker to search for
    :return: The number of pages
    """
    url = f'https://search.codal.ir/api/search/v2/q?&Audited=true&AuditorRef=-1&Category=3&Childs=false&CompanyState=0&CompanyType=3&Consolidatable=true&IsNotAudited=false&Isic=46430613&Length=-1&LetterType=-1&Mains=true&NotAudited=true&NotConsolidatable=true&PageNumber=1&Publisher=false&Symbol={converted_symbol}&TracingNo=-1&search=true'
    response = requests.get(url, headers=headers)
    pages = json.loads(response.text)['Page']
    logging.info(f'Found {pages} pages for "{symbol}"')
    return pages

def get_links_for_page(converted_symbol, page):
    """
    Get the links for a given page and ticker
    :param ticker: The ticker to search for
    :param page: The page number
    :return: A list of links
    """
    page_url = f'https://search.codal.ir/api/search/v2/q?&Audited=true&AuditorRef=-1&Category=3&Childs=false&CompanyState=0&CompanyType=3&Consolidatable=true&IsNotAudited=false&Isic=46430613&Length=-1&LetterType=-1&Mains=true&NotAudited=true&NotConsolidatable=true&PageNumber={page+1}&Publisher=false&Symbol={converted_symbol}&TracingNo=-1&search=true'
    response = requests.get(page_url, headers=headers)
    reports = json.loads(response.text)['Letters']
    
    for report in reports:
        AttachmentUrl = report['AttachmentUrl']
        Title = report['Title'].replace('/', '')
        TracingNo = report['TracingNo']
        links0[TracingNo] = [AttachmentUrl, Title]
    logging.info(f'Found {len(links0)} links for page {page+1}')
    return links0

def get_download_links(ticker_dir, symbol, links0):
    """
    Get the download links for a list of links
    :param links: A list of links
    :return: A list of download links
    """
    download_links = {}
    failed_links = []
    #files = os.listdir(ticker_dir)
    files = [f.split('.')[0] for f in os.listdir(ticker_dir)]
    for key, value in links0.items():
        f_name = f'{symbol} {value[1]} {key}'
        if f_name in files:
            continue
        else:
            url = f'https://www.codal.ir{value[0]}'
            response = requests.get(url, headers=headers)
            page_source = response.text
            match = re.search(r'DownloadFile\.aspx\?id=[^&#]+', page_source)
            if match:
                download_id = match.group(0)
                download_link = f'https://www.codal.ir/Reports/{download_id}'
                download_links[key] = [download_link, value[1]]
            else:
                logging.error(f'Failed to get download link for {symbol} {url}')
                failed_links.append(url)
                download_link = f'https://www.codal.ir/Reports/'
                download_links[key] = [download_link, value[1]]
    return download_links

def download_files(symbol, download_links):
    """
    Download the files for a list of download links
    :param download_links: A list of download links
    :param links: A list of links
    :return: A list of failed downloads
    """
    err = 'خطای سیستمی | کدال'
    exl_type = '[Content_Types].xml'
    counter = 0
    for key, value in download_links.items():
        counter += 1
        if len(value[0]) <= 29:
            logging.error(f'Error: {counter} of {len(download_links)} there is no download link {symbol} {value[1]} {key}')
            download_failed.append(f'{symbol} {value[1]} {key}')
            continue

        response = requests.get(value[0], headers=headers)
        if err in response.text[:100]:
            logging.error(f'Error: {counter} of {len(download_links)} {err} {symbol}_{value[1]}_{key}')
            download_failed.append(f'{symbol}_{value[1]}_{key}')
            continue
        if exl_type in response.text[:100]:
            file_format = 'xlsx'
        else:
            file_format = 'pdf'
        
        file_name = f'{symbol} {value[1]} {key}.{file_format}'
        with open(file_name, 'wb') as f:
            f.write(response.content)
            clear_output(wait=True)
            print(f'saved: {counter} of {len(download_links)} {symbol} {value[1]} {key}.{file_format}\n')
                
for symbol in symbols:
    converted = convert(symbol)
    folder = make_dir(symbol)
    initial_file_count = file_counter(folder)
    pages = get_pages_count(symbol, converted)
    for page in range(pages):
        page_links = get_links_for_page(converted, page)
    download_links = get_download_links(folder, symbol, page_links)
    download_files(symbol, download_links)
    final_file_count = file_counter(folder)
    print(f'Directory "{folder}" created for "{symbol}"')
    print(f'{symbol} {final_file_count - initial_file_count} file downloaded')
    print(f'failed: \n{download_failed}')

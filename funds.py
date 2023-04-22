import requests
import urllib.parse
import json
import re
import logging
from pathlib import Path
import os
from IPython.display import clear_output

logging.basicConfig(level=logging.INFO)

headers = {"User-Agent" : "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/111.0"}
symbol = 'کاردان'    # put your desired symbol
download_failed = []
main_dir = str(Path.home() / "Downloads")

def make_dir(symbol):
    """
    Create a directory for a given ticker
    :param ticker: The ticker to search for
    :return: ''
    """
    try:
        os.chdir(main_dir)
        os.mkdir(f'{symbol}')
        ticker_dir = f'{main_dir}\{symbol}'
        os.chdir(ticker_dir)
        logging.info(f'Directory "{ticker_dir}" created for "{symbol}"')
    except FileExistsError:
        ticker_dir = f'{main_dir}\{symbol}'
        os.chdir(ticker_dir)
        logging.info(f'Directory "{ticker_dir}" created for "{symbol}"')
        pass

def get_pages_count(symbol):
    """
    Get the number of pages for a given ticker
    :param ticker: The ticker to search for
    :return: The number of pages
    """
    ticker = urllib.parse.quote(symbol, encoding='utf-8')
    url = f'https://search.codal.ir/api/search/v2/q?&Audited=true&AuditorRef=-1&Category=3&Childs=false&CompanyState=0&CompanyType=3&Consolidatable=true&IsNotAudited=false&Isic=46430613&Length=-1&LetterType=-1&Mains=true&NotAudited=true&NotConsolidatable=true&PageNumber=1&Publisher=false&Symbol={ticker}&TracingNo=-1&search=true'
    response = requests.get(url, headers=headers)
    pages = json.loads(response.text)['Page']
    logging.info(f'Found {pages} pages for "{symbol}"')
    return pages

def get_links_for_page(symbol, page):
    """
    Get the links for a given page and ticker
    :param ticker: The ticker to search for
    :param page: The page number
    :return: A list of links
    """
    ticker = urllib.parse.quote(symbol, encoding='utf-8')
    page_url = f'https://search.codal.ir/api/search/v2/q?&Audited=true&AuditorRef=-1&Category=3&Childs=false&CompanyState=0&CompanyType=3&Consolidatable=true&IsNotAudited=false&Isic=46430613&Length=-1&LetterType=-1&Mains=true&NotAudited=true&NotConsolidatable=true&PageNumber={page+1}&Publisher=false&Symbol={ticker}&TracingNo=-1&search=true'
    response = requests.get(page_url, headers=headers)
    reports = json.loads(response.text)['Letters']
    links = []
    for report in reports:
        AttachmentUrl = report['AttachmentUrl']
        Title = report['Title'].replace('/', '')
        TracingNo = report['TracingNo']
        links.append([AttachmentUrl, Title, TracingNo])
    logging.info(f'Found {len(links)} links for page {page+1}')
    return links

def get_download_links(links):
    """
    Get the download links for a list of links
    :param links: A list of links
    :return: A list of download links
    """
    download_links = []
    failed_links = []
    for j, link in enumerate(links):
        url = f'https://www.codal.ir{link[0]}'
        response = requests.get(url, headers=headers)
        page_source = response.text
        match = re.search(r'DownloadFile\.aspx\?id=[^&#]+', page_source)
        if match:
            download_id = match.group(0)
            download_link = f'https://www.codal.ir/Reports/{download_id}'
            download_links.append(download_link)
        else:
            logging.error(f'Failed to get download link for {url}')
            failed_links.append(url)
            download_link = f'https://www.codal.ir/Reports/'
            download_links.append(download_link)
    return download_links

def download_files(download_links, links):
    """
    Download the files for a list of download links
    :param download_links: A list of download links
    :param links: A list of links
    :return: A list of failed downloads
    """
    err = 'خطای سیستمی | کدال'
    exl_type = '[Content_Types].xml'
    counter = 0
    for dlink, link in zip(download_links, links):
        counter += 1
        if len(dlink) <= 29:
            logging.error(f'Error: {counter} of {len(download_links)} there is no download link {symbol} {link[1]} {link[2]}')
            download_failed.append(f'{symbol} {link[1]} {link[2]}')
            continue

        response = requests.get(dlink, headers=headers)
        if err in response.text[:100]:
            logging.error(f'Error: {counter} of {len(download_links)} {err} {symbol}_{link[1]}_{link[2]}')
            download_failed.append(f'{symbol}_{link[1]}_{link[2]}')
            continue
        if exl_type in response.text[:100]:
            file_format = 'xlsx'
        else:
            file_format = 'pdf'
        with open(f'{symbol} {link[1]} {link[2]}.{file_format}', 'wb') as f:
            f.write(response.content)
            clear_output(wait=True)
            print(f'saved: {counter} of {len(download_links)} {symbol} {link[1]} {link[2]}.{file_format}\n')
            
if __name__ == "__main__":
    make_dir(symbol)
    pages = get_pages_count(symbol)
    links = []
    for page in range(pages):
        page_links = get_links_for_page(symbol, page)
        links.extend(page_links)
    download_links = get_download_links(links)
    download_files(download_links, links)

    print(f'Directory "{main_dir}\{symbol}" created for "{symbol}"')
    print(f'failed: \n{download_failed}')

import requests
from bs4 import BeautifulSoup
import math

def fetch_publication_url(root_url: str, publications: int, group: int, all: bool = False, verbose: bool = False):
   pages = math.ceil(publications / group)
   url_list = [root_url + str(i) + '/' for i in range(1, pages + 1)]
   all_links = []  # Store all the links from all pages
  
   headers = {
       'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
       'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
       'Accept-Language': 'en-US,en;q=0.5',
       'Accept-Encoding': 'deflate',
       'Connection': 'keep-alive',
       'Upgrade-Insecure-Requests': '1',
       'Sec-Fetch-Mode': 'navigate',
       'Sec-Fetch-Site': 'same-origin',
       'Sec-Fetch-User': '?1',
       'Priority': 'u=0, i',
       'Pragma': 'no-cache',
       'Cache-Control': 'no-cache'
   }

   for url in url_list:
       if verbose:
           print(f"Fetching {url}...")
       res = requests.get(url, headers=headers)
       if res.status_code != 200:
           print(f"Failed to fetch {url}, status code: {res.status_code}")
           continue
      
       res.encoding = 'utf-8'
       soup = BeautifulSoup(res.content, 'html.parser')
       # print(soup)
       links = soup.find_all('a', class_='button')
       all_links.extend(link.get('href') for link in links if link.get('href') and link.text.strip() == "Read More")
      
   return all_links


def mine_links(links: list, all: bool = False, verbose: bool = False):
   all_downloads = []
   if not all:
       return links[:5]  # Return first 5 links for brevity
   else:
       for link in links:
           if verbose:
               print(f"Processing link: {link}")
           headers = {
               'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:141.0) Gecko/20100101 Firefox/141.0',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Language': 'en-US,en;q=0.5',
               'Accept-Encoding': 'deflate',
               'Connection': 'keep-alive',
               'Upgrade-Insecure-Requests': '1',
               'Sec-Fetch-Mode': 'navigate',
               'Sec-Fetch-Site': 'same-origin',
               'Sec-Fetch-User': '?1',
               'Priority': 'u=0, i',
               'Pragma': 'no-cache',
               'Cache-Control': 'no-cache'
           }
           res = requests.get(link, headers=headers)
           if res.status_code != 200:
               print(f"Failed to fetch {link}, status code: {res.status_code}")
               continue
           res.encoding = 'utf-8'
           soup = BeautifulSoup(res.content, 'html.parser')
           links = soup.find_all('a', class_='button')
           all_downloads.extend(link.get('href') for link in links if link.get('href') and link.text.strip() == "Download")


   return all_downloads


def download_files(link: str, path: str):
   headers = {
               'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:141.0) Gecko/20100101 Firefox/141.0',
               'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
               'Accept-Language': 'en-US,en;q=0.5',
               'Accept-Encoding': 'deflate',
               # 'Connection': 'keep-alive',
               'Upgrade-Insecure-Requests': '1',
               'Sec-Fetch-Mode': 'navigate',
               'Sec-Fetch-Site': 'none',
               'Sec-Fetch-User': '?1',
               'Priority': 'u=0, i',
               'Pragma': 'no-cache',
               'Cache-Control': 'no-cache'
           }
   response = requests.get(link, headers=headers)
   if response.status_code != 200:
       print(f"Failed to download {link}, status code: {response.status_code}")
       return


   response.encoding = 'utf-8'
   filename = link.split('/')[-1]
   filepath = f"{path}/{filename}"
   with open(filepath, 'wb') as file:
       file.write(response.content)
   print(f"Downloaded: {filename}")




if __name__ == "__main__":
   root_url = "https://csgjusticecenter.org/publications/page/"
   publications =  582
   group = 8
   links = fetch_publication_url(root_url, publications, group)
  
   print(f"Found {len(links)} links total")
   print("First few links:")
   for i, link in enumerate(links[:10]):  # Show first 10 links
       print(f"{i+1}. {link}")


   downloads = mine_links(links, all=True)
   print(f"Found {len(downloads)} download links")
   print("Download links:")
   for i, download in enumerate(downloads[:10]):  # Show first 10 download links
       print(f"{i+1}. {download}")


   for download in downloads:
       download_files(download, "downloads") 
   print("All files downloaded.")


from bs4 import BeautifulSoup
import requests
import logging
import random
import os
import sys
import time
from datetime import datetime
from tqdm import tqdm
import json
import re
import pandas as pd
#thiet lap logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scraper_test.log", encoding='utf-8'),
        logging.StreamHandler()
    ]
)


class NewsScrapervneconomy:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        #mo phong trinh duyet web
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://vneconomy.vn/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.data = []
        self.session = requests.Session()

        #tao thu muc dataset neu chua co
        try:
            os.makedirs(output_dir, exist_ok=True)
            subdirs = ["raw", "processed"]
            for subdir in subdirs:
                os.makedirs(os.path.join(output_dir, subdir), exist_ok=True)
        except Exception as e:
            logging.error(f"1.error :{str(e)}")
            sys.exit(1)

    #num_pages mac dinh la 150, neu co tham so truyen vao se thay doi
    #tim cac link bai bao trong trang vneconomy
    def scraper_vneconomy(self, num_pages=150):
        logging.info("truy cap trang vneconomy va bat dau th nhap")
        article_links = []

        #khoi tao danh sach cac chuyen muc , lap qua tung chuyen muc + tung trang -> tim cac link bai bao
        categories = [
            "tieu-diem", "dau-tu", "tai-chinh", "kinh-te-so",
            "kinh-te-xanh", "thi-truong", "nhip-cau-doanh-nghiep", "dia-oc",
            "kinh-te-the-gioi", "dan-sinh", "chung-khoan", "tieu-dung"
        ]
        for category in categories:
            for page in range(1, num_pages + 1):
                try:
                    urls = [
                        f"https://vneconomy.vn/{category}.htm?trang={page}"
                    ]
                    check = False
                    for url in urls:
                        logging.info(f"thu truy cap: {url}")
                        response = self.session.get(url, headers=self.headers, timeout=15)
                        if response.status_code == 200:
                            logging.info(f"truy cap thanh cong: {url}")
                            check = True
                            soup = BeautifulSoup(response.text, "html.parser")
                            articles = []
                            #tim cac bai viet trong trang chu qua tag(cac phan co the an de mo bai viet cu the)
                            selectors = [
                                "article.story"
                            ]
                            for selector in selectors:
                                found_articles = soup.select(selector)
                                if found_articles:
                                    articles.extend(found_articles)
                                    logging.info(f"tim thay {len(found_articles)} bai viet voi selector: {selector}")
                            if not articles:
                                logging.warning(f"2.khong tim thay bai viet trong {url}")
                                continue
                            
                            #sau khi tim duoc so cac bai bao can tim cac link cu the de truy cap vao bai bao
                            for article in articles:
                                #lap tim ra link bai bao dau tien tra ve cua tung article
                                link_selectors = [
                                    "h3.story__title > a", "figure.story__thumb > a",
                                    "a"
                                ]
                                for link_selector in link_selectors:
                                    link = article.select_one(link_selector)
                                    #kiem tra link ton tai va co thuoc tinh href khong, neu co thi break
                                    if link and "href" in link.attrs:
                                        break
                                #dam bao link day du va dung dinh dang vi trang vneconomy chua cac link rut gon
                                if link and "href" in link.attrs:
                                    href = link["href"]
                                    if not href.startswith("http"):
                                        href = f"https://vneconomy.vn/{href}"
                                    article_links.append({
                                        "url": href,
                                        "source": "vneconomy",
                                        "category": category
                                    })
                            
                            logging.info(f"da thu thap {len(article_links)} lien ket tu vneconomy - chuyen muc {category} - trang {page}")
                            break
                        else:
                            logging.warning(f"3.khong the truy cap {url}, ma trang thai:{response.status_code}")
                    if check == False:
                        logging.error(f"4.khong the truy cap trang cho chuyen muc{category} trang {page}")
                    
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logging.error(f"5.loi khi thu thap lien ket tu chuyen muc {category} trang {page}: {str(e)}")
                    time.sleep(random.uniform(5, 10))

        #loai bo link trung nhau
        unique_links = []
        unique_urls = set()
        for link in article_links:
            if link["url"] not in unique_urls:
                unique_urls.add(link["url"])
                unique_links.append(link)
        logging.info(f"tong so lien ket duy nhat: {len(unique_links)}")

        for article_info in tqdm(unique_links, desc="Thu thập bài viết vneconomy"):
            try:
                article_data = self.scraper_vneconomy_article(article_info['url'], article_info['category'])
                if article_data:
                    self.data.append(article_data)
                    self._save_raw_article(article_data)
                    time.sleep(random.uniform(1, 3))
            except Exception as e:
                logging.error(f"6.Lỗi khi thu thập bài viết từ {article_info['url']}: {str(e)}")

        logging.info(f"da hoan thanh thu nhap tu vneconomy: {len(self.data)} bai viet")            


    #thu nhap noi dung tu bai viet, bao gom title, summary, content va category
    def scraper_vneconomy_article(self, url, category):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = self.session.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    logging.warning(f"7.khong the truy cap {url}, ma trang thai:{response.status_code}")
                    retry_count += 1
                    time.sleep(random.uniform(2, 5))
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")

                tittle = soup.select_one("h1.detail__title").text.strip()
                if not tittle:
                    logging.warning(f"8.khong tim thay tieu de trong {url}")
                
                summary = soup.select_one("h2.detail__summary").text.strip()
                if not summary:
                    logging.warning(f"9.khong tim thay tom tat trong {url}")
               
                content_elements = soup.select("div.detail__content > p")
                content = "\n".join([p.text.strip() for p in content_elements if p.text.strip()])

                return {
                    "title": tittle,
                    "summary": summary,
                    "content": content,
                    "category": category
                }
            except requests.exceptions.RequestException as e:
                retry_count += 1
                logging.warning(f"10.loi khi thu thap bai viet (lan {retry_count}/{max_retries}): {url}")
                if retry_count == max_retries:
                    logging.error(f"11.loi khi thu thap bai viet sau {max_retries} lan thu: {url}")
                    return None
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                logging.error(f"12.loi khong xac dinh khi xu ly bai viet {url}: {str(e)}")
                return None
        
        return None
    
    #luu du lieu thu nhap vao file json ra file raw
    def _save_raw_article(self, article_data):
        try:
            file_name = f"data_news_{int(time.time())}_{random.randint(1000, 9999)}.json"
            with open(os.path.join(self.output_dir, "raw", file_name), "w", encoding="utf-8") as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"13.loi khi luu du lieu thu: {str(e)}")

    # tien xu ly du lieu, xet tu self.data
    def preprocess_data(self):
        logging.info("bat dau tien xu ly du lieu")
        try:
            processed_data = []
            for article in tqdm(self.data, desc=" tien xu ly du lieu"):
                processed_article = self.clear_article(article)
                if processed_article:
                    processed_data.append(processed_article)
            df = pd.DataFrame(processed_data)
            df.to_csv(os.path.join(self.output_dir, "processed", "all_articles.csv"), header=True, index=False, encoding="utf-8")
            logging.info(f"da hoan thanh tien xu ly du lieu: {len(processed_data)} bai viet")
            return processed_data
        except Exception as e:
            logging.error(f"14.loi khi tien xu ly du lieu: {str(e)}")
            return []
    
    def clear_article(self, article):
        try:
            if not all(k in article for k in ['title', 'summary', 'content']):
                logging.warning(f"bai viet khong day du du lieu: {article}")
                return None
            
            title = self.clear_text(article['title'])
            summary = self.clear_text(article['summary'])
            content = self.clear_text(article['content'])
            category = self.clear_text(article['category'])

            clear_article = {
                "title" : title,
                "summary" : summary,
                "content" : content,
                "category" : category
            }
            return clear_article
            
        except Exception as e:
            logging.error(f"15.loi khi lam sach bai viet: {str(e)}")
            return None

    def clear_text(self, text):
        if not text:
            return ""
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'\s+', ' ', text) 
        text = re.sub(r'[^\w\s\.,;:!?""()-]', '', text)
        return text.strip()

    def run_scraper(self, pages_per_source=1):
        start_time = time.time()
        logging.info(f"bat dau qua trinh thu nhap du lieu")
        self.scraper_vneconomy(pages_per_source)

        self.preprocess_data()

        end_time = time.time()
        logging.info(f"da hoan thanh qua trinh thu nhap du lieu")
        logging.info(f"tong so bai viet da thu thap: {len(self.data)}")



class NewsScrapervnexpress:
    def __init__(self, output_dir="data"):
        self.output_dir = output_dir
        #mo phong trinh duyet web
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'vi,en-US;q=0.9,en;q=0.8',
            'Connection': 'keep-alive',
            'Referer': 'https://vnexpress.net/',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'same-origin',
            'Sec-Fetch-User': '?1',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        }
        self.data = []
        self.session = requests.Session()

    #num_pages mac dinh la 150, neu co tham so truyen vao se thay doi
    #tim cac link bai bao trong trang vneconomy
    def scraper_vnexpress(self, num_pages=150):
        logging.info("truy cap trang vnexpress va bat dau th nhap")
        article_links = []

        #khoi tao danh sach cac chuyen muc , lap qua tung chuyen muc + tung trang -> tim cac link bai bao
        categories = [
            "thoi-su", "the-gioi", "kinh-doanh", "cong-nghe", 
            "khoa-hoc", "bat-dong-san", "suc-khoe", "the-thao",
            "giai-tri", "phap-luat", "giao-duc", "doi-song",
            "oto-xe-may", "du-lich"
        ]
        for category in categories:
            for page in range(1, num_pages + 1):
                try:
                    urls = [
                        f"https://vnexpress.net/{category}-p{page}"
                    ]
                    check = False
                    for url in urls:
                        logging.info(f"thu truy cap: {url}")
                        response = self.session.get(url, headers=self.headers, timeout=15)
                        if response.status_code == 200:
                            logging.info(f"truy cap thanh cong: {url}")
                            check = True
                            soup = BeautifulSoup(response.text, "html.parser")
                            articles = []
                            #tim cac bai viet trong trang chu qua tag(cac phan co the an de mo bai viet cu the)
                            selectors = [
                                "article.item-news", "div.wrapper-topstory-folder"
                            ]
                            for selector in selectors:
                                found_articles = soup.select(selector)
                                if found_articles:
                                    articles.extend(found_articles)
                                    logging.info(f"tim thay {len(found_articles)} bai viet voi selector: {selector}")
                            if not articles:
                                logging.warning(f"16.khong tim thay bai viet trong {url}")
                                continue
                            
                            #sau khi tim duoc so cac bai bao can tim cac link cu the de truy cap vao bai bao
                            for article in articles:
                                #lap tim ra link bai bao dau tien tra ve cua tung article
                                link_selectors = [
                                    "h3.title-news > a", "p.description> a",
                                ]
                                for link_selector in link_selectors:
                                    link = article.select_one(link_selector)
                                    #kiem tra link ton tai va co thuoc tinh href khong, neu co thi break
                                    if link and "href" in link.attrs:
                                        break
                                #dam bao link day du va dung dinh dang vi trang vnexpress chua cac link rut gon
                                if link and "href" in link.attrs:
                                    href = link["href"]
                                    if not href.startswith("http"):
                                        href = f"https://vnexpress.net/{href}"
                                    article_links.append({
                                        "url": href,
                                        "source": "vnexpress",
                                        "category": category
                                    })
                            
                            logging.info(f"da thu thap {len(article_links)} lien ket tu vnexpress - chuyen muc {category} - trang {page}")
                            break
                        else:
                            logging.warning(f"17.khong the truy cap {url}, ma trang thai:{response.status_code}")
                    if check == False:
                        logging.error(f"18.khong the truy cap trang cho chuyen muc{category} trang {page}")
                    
                    time.sleep(random.uniform(2, 4))
                except Exception as e:
                    logging.error(f"19.loi khi thu thap lien ket tu chuyen muc {category} trang {page}: {str(e)}")
                    time.sleep(random.uniform(5, 10))

        #loai bo link trung nhau
        unique_links = []
        unique_urls = set()
        for link in article_links:
            if link["url"] not in unique_urls:
                unique_urls.add(link["url"])
                unique_links.append(link)
        logging.info(f"tong so lien ket duy nhat: {len(unique_links)}")

        for article_info in tqdm(unique_links, desc="Thu thập bài viết vnexpress"):
            try:
                article_data = self.scraper_vnexpress_article(article_info['url'], article_info['category'])
                if article_data:
                    self.data.append(article_data)
                    self._save_raw_article(article_data)
                    time.sleep(random.uniform(1, 3))
            except Exception as e:
                logging.error(f"20.Lỗi khi thu thập bài viết từ {article_info['url']}: {str(e)}")

        logging.info(f"da hoan thanh thu nhap tu vnexpress: {len(self.data)} bai viet")            


    #thu nhap noi dung tu bai viet, bao gom title, summary, content va category
    def scraper_vnexpress_article(self, url, category):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                response = self.session.get(url, headers=self.headers, timeout=15)
                if response.status_code != 200:
                    logging.warning(f"21.khong the truy cap {url}, ma trang thai:{response.status_code}")
                    retry_count += 1
                    time.sleep(random.uniform(2, 5))
                    continue
                
                soup = BeautifulSoup(response.text, "html.parser")

                tittle = soup.select_one("h1.title-detail").text.strip()
                if not tittle:
                    logging.warning(f"22.khong tim thay tieu de trong {url}")
                
                summary = soup.select_one("p.description").text.strip()
                if not summary:
                    logging.warning(f"23.khong tim thay tom tat trong {url}")
               
                content_elements = soup.select("article.fck_detail > p")
                content = "\n".join([p.text.strip() for p in content_elements if p.text.strip()])

                return {
                    "title": tittle,
                    "summary": summary,
                    "content": content,
                    "category": category
                }
            except requests.exceptions.RequestException as e:
                retry_count += 1
                logging.warning(f"24.loi khi thu thap bai viet (lan {retry_count}/{max_retries}): {url}")
                if retry_count == max_retries:
                    logging.error(f"25.loi khi thu thap bai viet sau {max_retries} lan thu: {url}")
                    return None
                time.sleep(random.uniform(3, 6))
            except Exception as e:
                logging.error(f"26.loi khong xac dinh khi xu ly bai viet {url}: {str(e)}")
                return None
        
        return None
    
    #luu du lieu thu nhap vao file json ra file raw
    def _save_raw_article(self, article_data):
        try:
            file_name = f"data_news_{int(time.time())}_{random.randint(1000, 9999)}.json"
            with open(os.path.join(self.output_dir, "raw", file_name), "w", encoding="utf-8") as f:
                json.dump(article_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"27.loi khi luu du lieu thu: {str(e)}")

    # tien xu ly du lieu, xet tu self.data
    def preprocess_data(self):
        logging.info("bat dau tien xu ly du lieu")
        try:
            processed_data = []
            for article in tqdm(self.data, desc=" tien xu ly du lieu"):
                processed_article = self.clear_article(article)
                if processed_article:
                    processed_data.append(processed_article)
            df = pd.DataFrame(processed_data)
            df.to_csv(os.path.join(self.output_dir, "processed", "all_articles.csv"), mode="a", header=False, index=False, encoding="utf-8")
            logging.info(f"da hoan thanh tien xu ly du lieu: {len(processed_data)} bai viet")
            return processed_data
        except Exception as e:
            logging.error(f"28.loi khi tien xu ly du lieu: {str(e)}")
            return []
    
    def clear_article(self, article):
        try:
            if not all(k in article for k in ['title', 'summary', 'content']):
                logging.warning(f"bai viet khong day du du lieu: {article}")
                return None
            
            title = self.clear_text(article['title'])
            summary = self.clear_text(article['summary'])
            content = self.clear_text(article['content'])
            category = self.clear_text(article['category'])

            clear_article = {
                "title" : title,
                "summary" : summary,
                "content" : content,
                "category" : category
            }
            return clear_article
            
        except Exception as e:
            logging.error(f"29.loi khi lam sach bai viet: {str(e)}")
            return None

    def clear_text(self, text):
        if not text:
            return ""
        text = re.sub(r'<.*?>', '', text)
        text = re.sub(r'\s+', ' ', text) 
        text = re.sub(r'[^\w\s\.,;:!?""()-]', '', text)
        return text.strip()

    def run_scraper(self, pages_per_source=1):
        start_time = time.time()
        logging.info(f"bat dau qua trinh thu nhap du lieu")
        self.scraper_vnexpress(pages_per_source)

        self.preprocess_data()

        end_time = time.time()
        logging.info(f"da hoan thanh qua trinh thu nhap du lieu")
        logging.info(f"tong so bai viet da thu thap: {len(self.data)}")

class finalprocessdata:
    def __init__(self, df):
        self.df = df
    def final_process(self):
        self.df = pd.read_csv("data/processed/all_articles.csv")
        self.df.dropna(subset=["content", "summary", "tittle", "category"], inplace=True)
        self.df = self.df[
                self.df["content"].apply(lambda x: len(str(x).split()) > 40) &
                self.df["summary"].apply(lambda x: len(str(x).split()) > 20) &
                self.df["title"].apply(lambda x: len(str(x).split()) > 10)
                ]
        self.df.to_csv("data/processed/vietnamese_news_data.csv", index=False)

    
if __name__ == "__main__":
    try:
        page = 200
        scraper1 = NewsScrapervneconomy()
        scraper1.run_scraper(pages_per_source=page)

        scraper2 = NewsScrapervnexpress()
        scraper2.run_scraper(pages_per_source=page)

        df = pd.read_csv("data/processed/all_articles.csv")
        data = finalprocessdata(df)
        data.final_process()

    except KeyboardInterrupt:
        logging.info("da nhan duoc ky lenh dung chuong trinh")
        sys.exit(0)
    except Exception as e:
        logging.error(f"30.loi khong xac dinh: {str(e)}")
        sys.exit(1)
        
        
        
    
                    

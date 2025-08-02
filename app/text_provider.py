import requests
from bs4 import BeautifulSoup
from urllib.parse import quote
import time

class BibleTextProvider:
    def __init__(self):
        self.cache = {}
        self.version = 'web'

    def fetch_chapter_text_api(self, book, chapter):
        try:
            api_url = "https://labs.bible.org/api/"
            params = {
                'passage': f"{book} {chapter}",
                'type': 'json',
                'formatting': 'plain'
            }
            response = requests.get(api_url, params=params, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data:
                    verses = [f"{v.get('verse')}. {v.get('text')}" for v in data]
                    return "\n".join(verses)
        except Exception:
            pass
        return None

    def fetch_chapter_text_web(self, book, chapter):
        try:
            url = f"https://www.biblegateway.com/passage/?search={quote(book)}+{chapter}&version=WEB&interface=print"
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                div = soup.find('div', class_='passage-text')
                if div:
                    for tag in div.find_all(['sup', 'div'], class_=['footnote', 'crossreference']):
                        tag.decompose()
                    paragraphs = div.find_all('p')
                    verses = [p.get_text().strip() for p in paragraphs if p.get_text().strip()]
                    return "\n\n".join(verses)
        except Exception as e:
            print(f"Error fetching from web: {e}")
        return None

    def get_fallback_text(self, book, chapter):
        return f"""
{book} Chapter {chapter}
[Bible text temporarily unavailable - please read from your preferred Bible]
"""

    def get_chapter_text(self, book, chapter):
        cache_key = f"{book}_{chapter}_{self.version}"
        if cache_key in self.cache:
            return self.cache[cache_key]
        text = self.fetch_chapter_text_api(book, chapter) or                self.fetch_chapter_text_web(book, chapter) or                self.get_fallback_text(book, chapter)
        self.cache[cache_key] = text
        time.sleep(0.5)
        return text

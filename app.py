#!/usr/bin/env python3
"""
Bible RSS Feed Generator with Full Text
Enhanced version with persistent caching, better error handling, and Railway optimizations

Install dependencies:
pip install flask flask-compress requests beautifulsoup4
"""

from flask import Flask, Response, request, render_template_string
from flask_compress import Compress
import requests
import json
import threading
from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from urllib.parse import quote, urljoin
import re
import time
from bs4 import BeautifulSoup
import os
import pickle
import signal
import sys

app = Flask(__name__)
Compress(app)

# Configuration

class Config:
CACHE_EXPIRY_DAYS = int(os.environ.get('CACHE_EXPIRY_DAYS', 30))
MAX_DAYS_TO_GENERATE = int(os.environ.get('MAX_DAYS_TO_GENERATE', 5))
DEFAULT_BIBLE_VERSION = os.environ.get('DEFAULT_BIBLE_VERSION', 'web')
CACHE_FILE = os.environ.get('CACHE_FILE', 'bible_cache.pkl')
PORT = int(os.environ.get('PORT', 5000))

class PersistentCache:
def __init__(self, cache_file='bible_cache.pkl', expiry_days=30):
self.cache_file = cache_file
self.expiry_delta = timedelta(days=expiry_days)
self.cache = self._load_cache()
self.unsaved_changes = False

```
def _load_cache(self):
    if os.path.exists(self.cache_file):
        try:
            with open(self.cache_file, 'rb') as f:
                cache = pickle.load(f)
            # Clean expired entries
            now = datetime.now()
            cleaned = {k: v for k, v in cache.items() 
                      if now - v['timestamp'] < self.expiry_delta}
            print(f"Loaded cache with {len(cleaned)} valid entries")
            return cleaned
        except Exception as e:
            print(f"Error loading cache: {e}")
            return {}
    return {}

def get(self, key):
    if key in self.cache:
        entry = self.cache[key]
        if datetime.now() - entry['timestamp'] < self.expiry_delta:
            return entry['data']
        else:
            # Remove expired entry
            del self.cache[key]
            self.unsaved_changes = True
    return None

def set(self, key, value):
    self.cache[key] = {
        'data': value,
        'timestamp': datetime.now()
    }
    self.unsaved_changes = True
    # Save every 10 changes
    if len(self.cache) % 10 == 0:
        self._save_cache()

def _save_cache(self):
    try:
        with open(self.cache_file, 'wb') as f:
            pickle.dump(self.cache, f)
        self.unsaved_changes = False
        print(f"Saved cache with {len(self.cache)} entries")
    except Exception as e:
        print(f"Error saving cache: {e}")

def force_save(self):
    if self.unsaved_changes:
        self._save_cache()
```

class BibleTextProvider:
def __init__(self):
self.cache = PersistentCache(Config.CACHE_FILE, Config.CACHE_EXPIRY_DAYS)
self.base_urls = {
'web': 'https://ebible.org/web/',  # World English Bible
'asv': 'https://ebible.org/asv/',  # American Standard Version
}
self.version = Config.DEFAULT_BIBLE_VERSION

```
def get_book_filename(self, book_name):
    """Convert book name to filename used by eBible.org"""
    book_mapping = {
        'Genesis': 'GEN', 'Exodus': 'EXO', 'Leviticus': 'LEV', 'Numbers': 'NUM',
        'Deuteronomy': 'DEU', 'Joshua': 'JOS', 'Judges': 'JDG', 'Ruth': 'RUT',
        '1 Samuel': '1SA', '2 Samuel': '2SA', '1 Kings': '1KI', '2 Kings': '2KI',
        '1 Chronicles': '1CH', '2 Chronicles': '2CH', 'Ezra': 'EZR', 'Nehemiah': 'NEH',
        'Esther': 'EST', 'Job': 'JOB', 'Psalms': 'PSA', 'Proverbs': 'PRO',
        'Ecclesiastes': 'ECC', 'Song of Solomon': 'SNG', 'Isaiah': 'ISA',
        'Jeremiah': 'JER', 'Lamentations': 'LAM', 'Ezekiel': 'EZK', 'Daniel': 'DAN',
        'Hosea': 'HOS', 'Joel': 'JOL', 'Amos': 'AMO', 'Obadiah': 'OBA', 'Jonah': 'JON',
        'Micah': 'MIC', 'Nahum': 'NAM', 'Habakkuk': 'HAB', 'Zephaniah': 'ZEP',
        'Haggai': 'HAG', 'Zechariah': 'ZEC', 'Malachi': 'MAL',
        'Matthew': 'MAT', 'Mark': 'MRK', 'Luke': 'LUK', 'John': 'JHN',
        'Acts': 'ACT', 'Romans': 'ROM', '1 Corinthians': '1CO', '2 Corinthians': '2CO',
        'Galatians': 'GAL', 'Ephesians': 'EPH', 'Philippians': 'PHP', 'Colossians': 'COL',
        '1 Thessalonians': '1TH', '2 Thessalonians': '2TH', '1 Timothy': '1TI',
        '2 Timothy': '2TI', 'Titus': 'TIT', 'Philemon': 'PHM', 'Hebrews': 'HEB',
        'James': 'JAS', '1 Peter': '1PE', '2 Peter': '2PE', '1 John': '1JN',
        '2 John': '2JN', '3 John': '3JN', 'Jude': 'JUD', 'Revelation': 'REV'
    }
    return book_mapping.get(book_name, book_name.upper()[:3])

def fetch_chapter_text_api(self, book, chapter):
    """Fetch chapter text using Bible API"""
    try:
        # Try Bible API first
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
                verses = []
                for verse_data in data:
                    verse_num = verse_data.get('verse', '')
                    verse_text = verse_data.get('text', '')
                    verses.append(f"{verse_num}. {verse_text}")
                return "\n".join(verses)
    except Exception as e:
        print(f"API fetch error for {book} {chapter}: {e}")
    return None

def fetch_chapter_text_web(self, book, chapter):
    """Fetch chapter text from web sources"""
    try:
        # Try Bible Gateway
        bg_url = f"https://www.biblegateway.com/passage/?search={quote(book)}+{chapter}&version=WEB&interface=print"
        headers = {'User-Agent': 'Mozilla/5.0 (compatible; BibleRSSReader/1.0)'}
        response = requests.get(bg_url, headers=headers, timeout=15)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Find the passage text
            passage_div = soup.find('div', class_='passage-text')
            if passage_div:
                # Remove footnotes and cross-references
                for unwanted in passage_div.find_all(['sup', 'div'], class_=['footnote', 'crossreference']):
                    unwanted.decompose()
                
                # Extract verse text
                verses = []
                for p in passage_div.find_all('p'):
                    text = p.get_text().strip()
                    if text:
                        verses.append(text)
                
                if verses:
                    return "\n\n".join(verses)
            
            # Fallback: try different selectors
            content_selectors = ['.passage-content', '.passage', '.text']
            for selector in content_selectors:
                content = soup.select_one(selector)
                if content:
                    text = content.get_text().strip()
                    if len(text) > 100:  # Reasonable chapter length
                        return text
    except Exception as e:
        print(f"Error fetching from web for {book} {chapter}: {e}")
    
    return None

def get_fallback_text(self, book, chapter):
    """Generate fallback content when text can't be fetched"""
    return f"""
```

{book} Chapter {chapter}

[Bible text temporarily unavailable - please read from your preferred Bible]

📖 Read online at:
• Bible Gateway: https://www.biblegateway.com/passage/?search={quote(book)}+{chapter}&version=ESV
• YouVersion: https://www.bible.com/search/bible?q={quote(book)}%20{chapter}
• Blue Letter Bible: https://www.blueletterbible.org/search/search.cfm?Criteria={quote(book)}+{chapter}

Today's Reading: {book} {chapter}

💡 Reading Tips:
• Read slowly and thoughtfully
• Look for key themes and applications
• Consider the historical context
• Pray for understanding and application

🙏 Prayer: "Lord, speak to me through Your Word today. Help me understand what You want to teach me through this passage. Amen."
""".strip()

```
def get_chapter_text(self, book, chapter):
    """Get the full text of a Bible chapter"""
    cache_key = f"{book}_{chapter}_{self.version}"
    
    # Check cache first
    cached_text = self.cache.get(cache_key)
    if cached_text:
        return cached_text
    
    print(f"Fetching {book} {chapter}...")
    
    # Try API first
    text = self.fetch_chapter_text_api(book, chapter)
    
    # If API fails, try web scraping
    if not text:
        text = self.fetch_chapter_text_web(book, chapter)
    
    # If all else fails, use fallback
    if not text:
        text = self.get_fallback_text(book, chapter)
    
    # Cache the result
    self.cache.set(cache_key, text)
    
    # Add a small delay to be respectful to servers
    time.sleep(0.5)
    
    return text
```

class BibleRSSGenerator:
def __init__(self):
self.text_provider = BibleTextProvider()
self.bible_books = {
'ot': [
('Genesis', 50), ('Exodus', 40), ('Leviticus', 27), ('Numbers', 36),
('Deuteronomy', 34), ('Joshua', 24), ('Judges', 21), ('Ruth', 4),
('1 Samuel', 31), ('2 Samuel', 24), ('1 Kings', 22), ('2 Kings', 25),
('1 Chronicles', 29), ('2 Chronicles', 36), ('Ezra', 10), ('Nehemiah', 13),
('Esther', 10), ('Job', 42), ('Ecclesiastes', 12), ('Song of Solomon', 8),
('Isaiah', 66), ('Jeremiah', 52), ('Lamentations', 5), ('Ezekiel', 48),
('Daniel', 12), ('Hosea', 14), ('Joel', 3), ('Amos', 9), ('Obadiah', 1),
('Jonah', 4), ('Micah', 7), ('Nahum', 3), ('Habakkuk', 3), ('Zephaniah', 3),
('Haggai', 2), ('Zechariah', 14), ('Malachi', 4)
],
'nt': [
('Matthew', 28), ('Mark', 16), ('Luke', 24), ('John', 21),
('Acts', 28), ('Romans', 16), ('1 Corinthians', 16), ('2 Corinthians', 13),
('Galatians', 6), ('Ephesians', 6), ('Philippians', 4), ('Colossians', 4),
('1 Thessalonians', 5), ('2 Thessalonians', 3), ('1 Timothy', 6),
('2 Timothy', 4), ('Titus', 3), ('Philemon', 1), ('Hebrews', 13),
('James', 5), ('1 Peter', 5), ('2 Peter', 3), ('1 John', 5),
('2 John', 1), ('3 John', 1), ('Jude', 1), ('Revelation', 22)
],
'psalms': [('Psalms', 150)],
'proverbs': [('Proverbs', 31)]
}

```
def get_bible_plan(self, plan_type):
    if plan_type == 'ot':
        return self.bible_books['ot']
    elif plan_type == 'nt':
        return self.bible_books['nt']
    elif plan_type == 'full':
        return self.bible_books['ot'] + self.bible_books['nt']
    elif plan_type == 'psalms':
        return self.bible_books['psalms']
    elif plan_type == 'proverbs':
        return self.bible_books['proverbs']
    else:
        raise ValueError("Plan type must be 'ot', 'nt', 'full', 'psalms', or 'proverbs'")

def get_mixed_plan_chapters(self, ot_per_day, nt_per_day, psalms_per_day, proverbs_per_day, start_date, target_date):
    """Get chapters for mixed reading plan (OT + NT + Psalms + Proverbs)"""
    days_elapsed = (target_date - start_date).days
    
    chapters_today = []
    
    # Old Testament chapters
    if ot_per_day > 0:
        ot_plan = self.bible_books['ot']
        ot_chapters = []
        for book_name, chapter_count in ot_plan:
            for chapter_num in range(1, chapter_count + 1):
                ot_chapters.append((book_name, chapter_num))
        
        ot_start = days_elapsed * ot_per_day
        for i in range(ot_per_day):
            chapter_idx = ot_start + i
            if chapter_idx < len(ot_chapters):
                chapters_today.append(ot_chapters[chapter_idx])
    
    # New Testament chapters
    if nt_per_day > 0:
        nt_plan = self.bible_books['nt']
        nt_chapters = []
        for book_name, chapter_count in nt_plan:
            for chapter_num in range(1, chapter_count + 1):
                nt_chapters.append((book_name, chapter_num))
        
        nt_start = days_elapsed * nt_per_day
        for i in range(nt_per_day):
            chapter_idx = nt_start + i
            if chapter_idx < len(nt_chapters):
                chapters_today.append(nt_chapters[chapter_idx])
    
    # Psalms (cycle through)
    if psalms_per_day > 0:
        psalms_start = days_elapsed * psalms_per_day
        for i in range(psalms_per_day):
            psalm_num = ((psalms_start + i) % 150) + 1  # Cycle through Psalms 1-150
            chapters_today.append(('Psalms', psalm_num))
    
    # Proverbs (cycle through)
    if proverbs_per_day > 0:
        proverbs_start = days_elapsed * proverbs_per_day
        for i in range(proverbs_per_day):
            proverb_num = ((proverbs_start + i) % 31) + 1  # Cycle through Proverbs 1-31
            chapters_today.append(('Proverbs', proverb_num))
    
    return chapters_today

def get_chapter_for_day(self, plan_type, start_date, chapters_per_day, target_date):
    plan = self.get_bible_plan(plan_type)
    days_elapsed = (target_date - start_date).days
    chapter_start = days_elapsed * chapters_per_day
    
    all_chapters = []
    for book_name, chapter_count in plan:
        for chapter_num in range(1, chapter_count + 1):
            all_chapters.append((book_name, chapter_num))
    
    chapters_today = []
    for i in range(chapters_per_day):
        chapter_idx = chapter_start + i
        if chapter_idx < len(all_chapters):
            chapters_today.append(all_chapters[chapter_idx])
    
    return chapters_today

def _generate_error_feed(self, error_message):
    """Generate a minimal valid RSS feed with error message"""
    rss = Element('rss')
    rss.set('version', '2.0')
    
    channel = SubElement(rss, 'channel')
    
    title = SubElement(channel, 'title')
    title.text = "Bible RSS Feed - Error"
    
    description = SubElement(channel, 'description')
    description.text = f"Error generating feed: {error_message}"
    
    link = SubElement(channel, 'link')
    link.text = request.host_url if request else "http://localhost:5000"
    
    item = SubElement(channel, 'item')
    item_title = SubElement(item, 'title')
    item_title.text = "Feed Generation Error"
    
    item_description = SubElement(item, 'description')
    item_description.text = f"An error occurred while generating your Bible reading feed: {error_message}"
    
    item_guid = SubElement(item, 'guid')
    item_guid.text = f"error-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    rough_string = tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')

def generate_rss_feed(self, plan_type, start_date_str, chapters_per_day=None, days_to_generate=None, 
                      ot_per_day=0, nt_per_day=0, psalms_per_day=0, proverbs_per_day=0):
    if days_to_generate is None:
        days_to_generate = Config.MAX_DAYS_TO_GENERATE
        
    try:
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Calculate how many days have passed since start date
        days_elapsed_since_start = (today - start_date).days
        
        # Determine the date range for feed generation
        if days_elapsed_since_start < 0:
            # Start date is in the future, begin from start date
            feed_start_date = start_date
            initial_day_number = 0
        else:
            # Start date is in the past, show recent entries
            # Show last 7 days of entries plus next 7 days
            days_to_show_before = 7
            feed_start_date = today - timedelta(days=days_to_show_before)
            
            # Make sure we don't go before the original start date
            if feed_start_date < start_date:
                feed_start_date = start_date
            
            initial_day_number = (feed_start_date - start_date).days
        
        # Generate up to 14 days in the future from today
        end_date = today + timedelta(days=14)
        
        # Pre-fetch all chapters with error recovery
        all_chapters_to_fetch = []
        current_date = feed_start_date
        current_day_number = initial_day_number
        
        while current_date <= end_date and len(all_chapters_to_fetch) < days_to_generate:
            if plan_type == 'mixed':
                chapters = self.get_mixed_plan_chapters(ot_per_day, nt_per_day, psalms_per_day, 
                                                      proverbs_per_day, start_date, current_date)
            else:
                chapters = self.get_chapter_for_day(plan_type, start_date, chapters_per_day, current_date)
            
            if not chapters:
                break
                
            all_chapters_to_fetch.append((current_date, chapters, current_day_number))
            current_date += timedelta(days=1)
            current_day_number += 1
        
        # Pre-fetch with error recovery
        fetched_data = {}
        total_chapters = sum(len(chapters) for _, chapters, _ in all_chapters_to_fetch)
        fetched_count = 0
        
        print(f"Pre-fetching {total_chapters} chapters for dates {feed_start_date.strftime('%Y-%m-%d')} to {current_date.strftime('%Y-%m-%d')}...")
        
        for date, chapters, day_num in all_chapters_to_fetch:
            for book, chapter in chapters:
                key = (book, chapter)
                if key not in fetched_data:
                    try:
                        fetched_data[key] = self.text_provider.get_chapter_text(book, chapter)
                        fetched_count += 1
                        if fetched_count % 10 == 0:
                            print(f"Fetched {fetched_count}/{total_chapters} chapters...")
                    except Exception as e:
                        print(f"Failed to fetch {book} {chapter}: {e}")
                        fetched_data[key] = self.text_provider.get_fallback_text(book, chapter)
        
        # Save cache after fetching
        self.text_provider.cache.force_save()
        
        # Generate RSS
        rss = Element('rss')
        rss.set('version', '2.0')
        rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
        rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
        
        channel = SubElement(rss, 'channel')
        
        title = SubElement(channel, 'title')
        if plan_type == 'mixed':
            parts = []
            if ot_per_day > 0: parts.append(f"{ot_per_day} OT")
            if nt_per_day > 0: parts.append(f"{nt_per_day} NT")
            if psalms_per_day > 0: parts.append(f"{psalms_per_day} Ps")
            if proverbs_per_day > 0: parts.append(f"{proverbs_per_day} Pr")
            title.text = f"Daily Bible Reading - Mixed Plan ({', '.join(parts)})"
        else:
            title.text = f"Daily Bible Reading - {plan_type.upper()} ({chapters_per_day} ch/day)"
        
        description = SubElement(channel, 'description')
        if plan_type == 'mixed':
            desc_parts = []
            if ot_per_day > 0: desc_parts.append(f"{ot_per_day} Old Testament")
            if nt_per_day > 0: desc_parts.append(f"{nt_per_day} New Testament")
            if psalms_per_day > 0: desc_parts.append(f"{psalms_per_day} Psalm(s)")
            if proverbs_per_day > 0: desc_parts.append(f"{proverbs_per_day} Proverb(s)")
            description.text = f"Daily mixed Bible reading: {', '.join(desc_parts)} per day"
        else:
            description.text = f"Complete Bible text for daily reading - {chapters_per_day} chapter{'s' if chapters_per_day > 1 else ''} per day"
        
        link = SubElement(channel, 'link')
        link.text = request.host_url if request else "http://localhost:5000"
        
        language = SubElement(channel, 'language')
        language.text = "en-us"
        
        last_build_date = SubElement(channel, 'lastBuildDate')
        last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Generate items using pre-fetched data
        for date, chapters, day_num in all_chapters_to_fetch:
            item = SubElement(channel, 'item')
            
            # Title - use the calculated day number
            item_title = SubElement(item, 'title')
            if len(chapters) == 1:
                item_title.text = f"Day {day_num + 1}: {chapters[0][0]} {chapters[0][1]} ({date.strftime('%b %d')})"
            else:
                # Group by book type for cleaner titles
                nt_books = ['Matthew', 'Mark', 'Luke', 'John', 'Acts', 'Romans', '1 Corinthians', '2 Corinthians', 
                           'Galatians', 'Ephesians', 'Philippians', 'Colossians', '1 Thessalonians', '2 Thessalonians', 
                           '1 Timothy', '2 Timothy', 'Titus', 'Philemon', 'Hebrews', 'James', '1 Peter', '2 Peter', 
                           '1 John', '2 John', '3 John', 'Jude', 'Revelation']
                
                title_parts = []
                for book, ch in chapters:
                    if book == 'Psalms':
                        title_parts.append(f"Ps {ch}")
                    elif book == 'Proverbs':
                        title_parts.append(f"Pr {ch}")
                    else:
                        title_parts.append(f"{book} {ch}")
                
                item_title.text = f"Day {day_num + 1}: {', '.join(title_parts)} ({date.strftime('%b %d')})"
            
            # Description with full Bible text
            item_description = SubElement(item, 'description')
            content_parts = []
            
            for book, chapter in chapters:
                chapter_text = fetched_data.get((book, chapter), self.text_provider.get_fallback_text(book, chapter))
                book_display = "Psalm" if book == "Psalms" else book
                content_parts.append(f"""
```

<div style="margin-bottom: 30px;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        📖 {book_display} {chapter}
    </h2>
    <div style="line-height: 1.6; font-family: 'Georgia', serif; white-space: pre-wrap; margin: 15px 0;">
{chapter_text}
    </div>
</div>
                    """.strip())

```
            # Add reflection section
            content_parts.append(f"""
```

<div style="background-color: #f8f9fa; padding: 15px; border-left: 4px solid #3498db; margin-top: 20px;">
    <h3 style="color: #2c3e50; margin-top: 0;">📝 Reflection Questions</h3>
    <ul style="line-height: 1.6;">
        <li>What stands out to you in today's reading?</li>
        <li>How does this passage reveal God's character?</li>
        <li>What is one thing you can apply from this reading?</li>
        <li>How do these passages connect with each other?</li>
    </ul>
    <p style="margin-bottom: 0;"><strong>🙏 Prayer:</strong> "Lord, thank you for Your Word. Help me understand and apply what I've read today. Amen."</p>
</div>
                """)

```
            full_content = ''.join(content_parts)
            item_description.text = f"<![CDATA[{full_content}]]>"
            
            # Link to online Bible
            item_link = SubElement(item, 'link')
            if len(chapters) == 1:
                book, ch = chapters[0]
                item_link.text = f"https://www.biblegateway.com/passage/?search={quote(book)}+{ch}&version=ESV"
            else:
                passages = "%3B".join([f"{quote(book)}+{ch}" for book, ch in chapters])
                item_link.text = f"https://www.biblegateway.com/passage/?search={passages}&version=ESV"
            
            # GUID
            item_guid = SubElement(item, 'guid')
            if plan_type == 'mixed':
                item_guid.text = f"bible-mixed-{date.strftime('%Y%m%d')}-{ot_per_day}ot-{nt_per_day}nt-{psalms_per_day}ps-{proverbs_per_day}pr"
            else:
                item_guid.text = f"bible-{plan_type}-{date.strftime('%Y%m%d')}-{chapters_per_day}ch"
            item_guid.set('isPermaLink', 'false')
            
            # Publication date (6 AM on reading day)
            item_pub_date = SubElement(item, 'pubDate')
            pub_datetime = date.replace(hour=6, minute=0, second=0, microsecond=0)
            item_pub_date.text = pub_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        # Convert to pretty XML
        rough_string = tostring(rss, 'utf-8')
        reparsed = minidom.parseString(rough_string)
        return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
        
    except Exception as e:
        print(f"Feed generation error: {e}")
        return self._generate_error_feed(str(e))
```

# Initialize generator

generator = BibleRSSGenerator()

# HTML Template with mixed plan improvements

HTML_TEMPLATE = """

<!DOCTYPE html>

<html>
<head>
    <title>Bible RSS Feed Generator with Full Text</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; }
        select, input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; width: 200px; }
        .mixed-controls { display: none; background: #f8f9fa; padding: 15px; border-radius: 4px; margin: 10px 0; }
        .mixed-group { display: flex; gap: 15px; flex-wrap: wrap; }
        .mixed-item { display: flex; flex-direction: column; }
        .mixed-item label { font-size: 13px; margin-bottom: 3px; }
        .mixed-item select { width: 60px; font-size: 13px; }
        #mixed-summary { margin-top: 10px; padding: 10px; background: #e3f2fd; border-radius: 4px; font-weight: 500; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .feed-url { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 15px 0; font-family: monospace; word-break: break-all; }
        .instructions { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .feature-highlight { background: #e8f5e8; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #4caf50; }
        .health-status { position: absolute; top: 10px; right: 10px; padding: 5px 10px; background: #4caf50; color: white; border-radius: 4px; font-size: 12px; }
    </style>
    <script>
        function toggleMixedControls() {
            const plan = document.getElementById('plan').value;
            const mixedControls = document.getElementById('mixed-controls');
            const regularControls = document.getElementById('regular-controls');

```
        if (plan === 'mixed') {
            mixedControls.style.display = 'block';
            regularControls.style.display = 'none';
            updateMixedPlanSummary();
        } else {
            mixedControls.style.display = 'none';
            regularControls.style.display = 'block';
        }
    }
    
    function updateMixedPlanSummary() {
        const ot = parseInt(document.getElementById('ot_chapters').value) || 0;
        const nt = parseInt(document.getElementById('nt_chapters').value) || 0;
        const ps = parseInt(document.getElementById('psalm_chapters').value) || 0;
        const pr = parseInt(document.getElementById('proverb_chapters').value) || 0;
        
        const total = ot + nt + ps + pr;
        const minTime = total * 3;
        const maxTime = total * 6;
        
        document.getElementById('mixed-summary').innerHTML = 
            `📊 Total: ${total} chapters/day (~${minTime}-${maxTime} minutes)`;
    }
    
    // Check health status
    async function checkHealth() {
        try {
            const response = await fetch('/health');
            if (response.ok) {
                document.getElementById('health-status').textContent = '✓ System Healthy';
            }
        } catch (e) {
            document.getElementById('health-status').textContent = '⚠ System Check Failed';
        }
    }
    
    window.onload = function() {
        checkHealth();
        setInterval(checkHealth, 30000); // Check every 30 seconds
    }
</script>
```

</head>
<body>
    <div id="health-status" class="health-status">Checking...</div>
    <h1>📖 Bible RSS Feed Generator</h1>
    <div class="feature-highlight">
        <h3>✨ Full Bible Text Included!</h3>
        <p>This generator includes the complete Bible text in your RSS feed, so you can read directly in your RSS reader without clicking external links.</p>
    </div>

```
<form action="/generate" method="get">
    <div class="form-group">
        <label for="plan">Reading Plan:</label>
        <select name="plan" id="plan" onchange="toggleMixedControls()">
            <option value="nt">New Testament Only (~260 chapters)</option>
            <option value="ot">Old Testament Only (~929 chapters)</option>
            <option value="full">Complete Bible (~1,189 chapters)</option>
            <option value="mixed">🌟 Mixed Plan (OT + NT + Psalms + Proverbs)</option>
        </select>
    </div>
    
    <div class="form-group" id="regular-controls">
        <label for="chapters">Chapters per Day:</label>
        <select name="chapters" id="chapters">
            <option value="1">1 Chapter (~3-4 minutes)</option>
            <option value="2">2 Chapters (~6-8 minutes)</option>
            <option value="3">3 Chapters (~9-12 minutes)</option>
            <option value="4">4 Chapters (~12-16 minutes)</option>
            <option value="5">5 Chapters (~15-20 minutes)</option>
        </select>
    </div>
    
    <div id="mixed-controls" class="mixed-controls">
        <h4>📚 Customize Your Mixed Reading Plan</h4>
        <p style="margin-bottom: 15px; font-size: 14px; color: #666;">
            Select how many chapters from each section you want to read daily. Psalms and Proverbs will cycle through automatically.
        </p>
        <div class="mixed-group">
            <div class="mixed-item">
                <label for="ot_chapters">Old Testament</label>
                <select name="ot_chapters" id="ot_chapters" onchange="updateMixedPlanSummary()">
                    <option value="0">0</option>
                    <option value="1" selected>1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                </select>
            </div>
            <div class="mixed-item">
                <label for="nt_chapters">New Testament</label>
                <select name="nt_chapters" id="nt_chapters" onchange="updateMixedPlanSummary()">
                    <option value="0">0</option>
                    <option value="1" selected>1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                </select>
            </div>
            <div class="mixed-item">
                <label for="psalm_chapters">Psalms</label>
                <select name="psalm_chapters" id="psalm_chapters" onchange="updateMixedPlanSummary()">
                    <option value="0">0</option>
                    <option value="1" selected>1</option>
                    <option value="2">2</option>
                    <option value="3">3</option>
                </select>
            </div>
            <div class="mixed-item">
                <label for="proverb_chapters">Proverbs</label>
                <select name="proverb_chapters" id="proverb_chapters" onchange="updateMixedPlanSummary()">
                    <option value="0">0</option>
                    <option value="1" selected>1</option>
                    <option value="2">2</option>
                </select>
            </div>
        </div>
        <div id="mixed-summary">📊 Total: 4 chapters/day (~12-24 minutes)</div>
        <p style="margin-top: 10px; font-size: 13px; color: #666;">
            💡 <strong>Tip:</strong> A balanced plan might include 2 OT + 1 NT + 1 Psalm daily. Psalms and Proverbs cycle continuously.
        </p>
    </div>
    
    <div class="form-group">
        <label for="start_date">Start Date:</label>
        <input type="date" name="start_date" id="start_date" value="{{ today }}">
    </div>
    
    <button type="submit">Generate RSS Feed with Full Text</button>
</form>

{% if feed_url %}
<div class="instructions">
    <h3>✅ Your RSS Feed is Ready!</h3>
    <p><strong>Feed URL:</strong></p>
    <div class="feed-url">{{ feed_url }}</div>
    <p><strong>What you get:</strong></p>
    <ul>
        <li>📖 Complete Bible text for each day's reading</li>
        <li>📝 Reflection questions and prayer prompts</li>
        <li>🔗 Links to online Bible for cross-referencing</li>
        <li>📅 Daily delivery at 6 AM</li>
    </ul>
    <p><strong>Setup Instructions:</strong></p>
    <ol>
        <li>Copy the feed URL above</li>
        <li>Add it to your RSS reader (Feedly, Inoreader, Apple News, etc.)</li>
        <li>New readings appear daily with full text</li>
    </ol>
</div>
{% endif %}

<div style="margin-top: 40px; padding-top: 20px; border-top: 1px solid #eee; color: #666; font-size: 14px;">
    <p>📊 <strong>Reading Time Estimates:</strong></p>
    <ul>
        <li>New Testament: ~3 months (1 ch/day) or ~1 month (3 ch/day)</li>
        <li>Old Testament: ~2.5 years (1 ch/day) or ~8 months (3 ch/day)</li>
        <li>Full Bible: ~3 years (1 ch/day) or ~1 year (3 ch/day)</li>
    </ul>
    <p><small>⚡ <strong>Note:</strong> Text is fetched dynamically when you first access the feed, then cached for performance. Cache persists across restarts.</small></p>
</div>
```

</body>
</html>
"""

@app.route('/')
def index():
today = datetime.now().strftime('%Y-%m-%d')
feed_url = request.args.get('feed_url')
return render_template_string(HTML_TEMPLATE, today=today, feed_url=feed_url)

@app.route('/health')
def health_check():
"""Health check endpoint for Railway"""
return {
'status': 'healthy',
'timestamp': datetime.now().isoformat(),
'cache_entries': len(generator.text_provider.cache.cache),
'version': '1.0.0'
}, 200

@app.route('/generate')
def generate_feed():
plan = request.args.get('plan', 'nt')
start_date = request.args.get('start_date', datetime.now().strftime('%Y-%m-%d'))

```
if plan == 'mixed':
    ot_chapters = int(request.args.get('ot_chapters', 1))
    nt_chapters = int(request.args.get('nt_chapters', 1))
    psalm_chapters = int(request.args.get('psalm_chapters', 1))
    proverb_chapters = int(request.args.get('proverb_chapters', 1))
    
    feed_url = f"{request.host_url}feed/mixed/{start_date}/{ot_chapters}-{nt_chapters}-{psalm_chapters}-{proverb_chapters}/feed.rss"
else:
    chapters = int(request.args.get('chapters', 1))
    feed_url = f"{request.host_url}feed/{plan}/{start_date}/{chapters}/feed.rss"

# Return the homepage with the feed URL displayed
today = datetime.now().strftime('%Y-%m-%d')
return render_template_string(HTML_TEMPLATE, today=today, feed_url=feed_url)
```

@app.route('/feed/<plan>/<start_date>/<int:chapters>/feed.rss')
def serve_feed(plan, start_date, chapters):
try:
print(f"Generating feed: {plan}, start_date={start_date}, {chapters} chapters/day")
print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
feed_content = generator.generate_rss_feed(plan, start_date, chapters_per_day=chapters)
response = Response(feed_content, mimetype='application/rss+xml')
response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
return response
except Exception as e:
print(f"Error: {e}")
import traceback
traceback.print_exc()
return f"Error generating feed: {str(e)}", 400

@app.route('/feed/mixed/<start_date>/<path:mixed_params>/feed.rss')
def serve_mixed_feed(start_date, mixed_params):
try:
# Parse mixed parameters: ot-nt-psalms-proverbs
params = mixed_params.split('-')
if len(params) != 4:
return "Invalid mixed plan parameters", 400

```
    ot_per_day = int(params[0])
    nt_per_day = int(params[1])
    psalms_per_day = int(params[2])
    proverbs_per_day = int(params[3])
    
    print(f"Generating mixed feed: start_date={start_date}, OT:{ot_per_day}, NT:{nt_per_day}, Ps:{psalms_per_day}, Pr:{proverbs_per_day}")
    print(f"Current date: {datetime.now().strftime('%Y-%m-%d')}")
    
    feed_content = generator.generate_rss_feed(
        'mixed', start_date, 
        ot_per_day=ot_per_day, 
        nt_per_day=nt_per_day, 
        psalms_per_day=psalms_per_day, 
        proverbs_per_day=proverbs_per_day
    )
    response = Response(feed_content, mimetype='application/rss+xml')
    response.headers['Cache-Control'] = 'public, max-age=3600'  # Cache for 1 hour
    return response
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
    return f"Error generating mixed feed: {str(e)}", 400
```

# Add caching headers

@app.after_request
def add_cache_headers(response):
if response.mimetype == 'application/rss+xml':
response.headers['Cache-Control'] = 'public, max-age=3600'
return response

# Graceful shutdown handling

def signal_handler(sig, frame):
print('Shutting down gracefully…')
# Save cache before shutdown
generator.text_provider.cache.force_save()
sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

def run_bible_rss_server():
"""
Run the Bible RSS server with full text

```
For Railway deployment, this will use the PORT environment variable
"""
print("🚀 Starting Bible RSS Feed Generator with Full Text...")
print(f"📁 Using cache file: {Config.CACHE_FILE}")
print(f"⏰ Cache expiry: {Config.CACHE_EXPIRY_DAYS} days")
print(f"📖 Default Bible version: {Config.DEFAULT_BIBLE_VERSION}")

# Load existing cache stats
if hasattr(generator.text_provider.cache, 'cache'):
    print(f"📊 Loaded {len(generator.text_provider.cache.cache)} cached chapters")

print("\n📚 Features:")
print("• Full Bible text in each RSS item")
print("• Multiple reading plans (OT, NT, Full Bible)")
print("• Mixed plan with customizable OT/NT/Psalms/Proverbs")
print("• Persistent caching across restarts")
print("• Health check endpoint at /health")
print("• Graceful shutdown with cache saving")

# Start the server
port = Config.PORT
print(f"\n🌐 Starting server on port {port}")
app.run(host='0.0.0.0', port=port, debug=False, threaded=True)
```

if __name__ == "__main__":
run_bible_rss_server()
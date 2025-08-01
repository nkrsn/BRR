#!/usr/bin/env python3
“””
Bible RSS Feed Generator with Full Text
Includes actual Bible text in RSS feed using World English Bible (public domain)

Install dependencies:
!pip install flask pyngrok requests beautifulsoup4
“””

from flask import Flask, Response, request, render_template_string
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

app = Flask(**name**)

class BibleTextProvider:
def **init**(self):
self.cache = {}
self.base_urls = {
‘web’: ‘https://ebible.org/web/’,  # World English Bible
‘asv’: ‘https://ebible.org/asv/’,  # American Standard Version
}
self.version = ‘web’  # Default to World English Bible (public domain)

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
    except:
        pass
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
        print(f"Error fetching from web: {e}")
    
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

Today’s Reading: {book} {chapter}

💡 Reading Tips:
• Read slowly and thoughtfully
• Look for key themes and applications
• Consider the historical context
• Pray for understanding and application

🙏 Prayer: “Lord, speak to me through Your Word today. Help me understand what You want to teach me through this passage. Amen.”
“””.strip()

```
def get_chapter_text(self, book, chapter):
    """Get the full text of a Bible chapter"""
    cache_key = f"{book}_{chapter}_{self.version}"
    
    # Check cache first
    if cache_key in self.cache:
        return self.cache[cache_key]
    
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
    self.cache[cache_key] = text
    
    # Add a small delay to be respectful to servers
    time.sleep(0.5)
    
    return text
```

class BibleRSSGenerator:
def **init**(self):
self.text_provider = BibleTextProvider()
self.bible_books = {
‘ot’: [
(‘Genesis’, 50), (‘Exodus’, 40), (‘Leviticus’, 27), (‘Numbers’, 36),
(‘Deuteronomy’, 34), (‘Joshua’, 24), (‘Judges’, 21), (‘Ruth’, 4),
(‘1 Samuel’, 31), (‘2 Samuel’, 24), (‘1 Kings’, 22), (‘2 Kings’, 25),
(‘1 Chronicles’, 29), (‘2 Chronicles’, 36), (‘Ezra’, 10), (‘Nehemiah’, 13),
(‘Esther’, 10), (‘Job’, 42), (‘Psalms’, 150), (‘Proverbs’, 31),
(‘Ecclesiastes’, 12), (‘Song of Solomon’, 8), (‘Isaiah’, 66),
(‘Jeremiah’, 52), (‘Lamentations’, 5), (‘Ezekiel’, 48), (‘Daniel’, 12),
(‘Hosea’, 14), (‘Joel’, 3), (‘Amos’, 9), (‘Obadiah’, 1), (‘Jonah’, 4),
(‘Micah’, 7), (‘Nahum’, 3), (‘Habakkuk’, 3), (‘Zephaniah’, 3),
(‘Haggai’, 2), (‘Zechariah’, 14), (‘Malachi’, 4)
],
‘nt’: [
(‘Matthew’, 28), (‘Mark’, 16), (‘Luke’, 24), (‘John’, 21),
(‘Acts’, 28), (‘Romans’, 16), (‘1 Corinthians’, 16), (‘2 Corinthians’, 13),
(‘Galatians’, 6), (‘Ephesians’, 6), (‘Philippians’, 4), (‘Colossians’, 4),
(‘1 Thessalonians’, 5), (‘2 Thessalonians’, 3), (‘1 Timothy’, 6),
(‘2 Timothy’, 4), (‘Titus’, 3), (‘Philemon’, 1), (‘Hebrews’, 13),
(‘James’, 5), (‘1 Peter’, 5), (‘2 Peter’, 3), (‘1 John’, 5),
(‘2 John’, 1), (‘3 John’, 1), (‘Jude’, 1), (‘Revelation’, 22)
]
}

```
def get_bible_plan(self, plan_type):
    if plan_type == 'ot':
        return self.bible_books['ot']
    elif plan_type == 'nt':
        return self.bible_books['nt']
    elif plan_type == 'full':
        return self.bible_books['ot'] + self.bible_books['nt']
    else:
        raise ValueError("Plan type must be 'ot', 'nt', or 'full'")

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

def generate_rss_feed(self, plan_type, start_date_str, chapters_per_day, days_to_generate=30):
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    
    rss = Element('rss')
    rss.set('version', '2.0')
    rss.set('xmlns:atom', 'http://www.w3.org/2005/Atom')
    rss.set('xmlns:content', 'http://purl.org/rss/1.0/modules/content/')
    
    channel = SubElement(rss, 'channel')
    
    title = SubElement(channel, 'title')
    title.text = f"Daily Bible Reading - {plan_type.upper()} ({chapters_per_day} ch/day)"
    
    description = SubElement(channel, 'description')
    description.text = f"Complete Bible text for daily reading - {chapters_per_day} chapter{'s' if chapters_per_day > 1 else ''} per day"
    
    link = SubElement(channel, 'link')
    link.text = request.host_url if request else "http://localhost:5000"
    
    language = SubElement(channel, 'language')
    language.text = "en-us"
    
    last_build_date = SubElement(channel, 'lastBuildDate')
    last_build_date.text = datetime.now().strftime('%a, %d %b %Y %H:%M:%S +0000')
    
    # Generate items
    current_date = start_date
    for day in range(days_to_generate):
        chapters = self.get_chapter_for_day(plan_type, start_date, chapters_per_day, current_date)
        
        if not chapters:
            break
            
        item = SubElement(channel, 'item')
        
        # Title
        item_title = SubElement(item, 'title')
        if len(chapters) == 1:
            item_title.text = f"Day {day + 1}: {chapters[0][0]} {chapters[0][1]} ({current_date.strftime('%b %d')})"
        else:
            chapter_list = ", ".join([f"{book} {ch}" for book, ch in chapters])
            item_title.text = f"Day {day + 1}: {chapter_list} ({current_date.strftime('%b %d')})"
        
        # Description with full Bible text
        item_description = SubElement(item, 'description')
        content_parts = []
        
        for book, chapter in chapters:
            chapter_text = self.text_provider.get_chapter_text(book, chapter)
            content_parts.append(f"""
```

<div style="margin-bottom: 30px;">
    <h2 style="color: #2c3e50; border-bottom: 2px solid #3498db; padding-bottom: 10px;">
        📖 {book} Chapter {chapter}
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
        <li>How does this connect to what you've read recently?</li>
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
        item_guid.text = f"bible-{plan_type}-{current_date.strftime('%Y%m%d')}-{chapters_per_day}ch"
        item_guid.set('isPermaLink', 'false')
        
        # Publication date (6 AM on reading day)
        item_pub_date = SubElement(item, 'pubDate')
        pub_datetime = current_date.replace(hour=6, minute=0, second=0, microsecond=0)
        item_pub_date.text = pub_datetime.strftime('%a, %d %b %Y %H:%M:%S +0000')
        
        current_date += timedelta(days=1)
    
    # Convert to pretty XML
    rough_string = tostring(rss, 'utf-8')
    reparsed = minidom.parseString(rough_string)
    return reparsed.toprettyxml(indent="  ", encoding='utf-8').decode('utf-8')
```

# Initialize generator

generator = BibleRSSGenerator()

# Web interface (same as before but with note about full text)

HTML_TEMPLATE = “””

<!DOCTYPE html>

<html>
<head>
    <title>Bible RSS Feed Generator with Full Text</title>
    <style>
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-weight: 500; }
        select, input { padding: 8px; border: 1px solid #ddd; border-radius: 4px; font-size: 14px; width: 200px; }
        button { background: #007cba; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; }
        button:hover { background: #005a87; }
        .feed-url { background: #f5f5f5; padding: 15px; border-radius: 4px; margin: 15px 0; font-family: monospace; word-break: break-all; }
        .instructions { background: #e3f2fd; padding: 15px; border-radius: 4px; margin: 15px 0; }
        .feature-highlight { background: #e8f5e8; padding: 15px; border-radius: 4px; margin: 15px 0; border-left: 4px solid #4caf50; }
    </style>
</head>
<body>
    <h1>📖 Bible RSS Feed Generator</h1>
    <div class="feature-highlight">
        <h3>✨ Full Bible Text Included!</h3>
        <p>This generator includes the complete Bible text in your RSS feed, so you can read directly in your RSS reader without clicking external links.</p>
    </div>

```
<form action="/generate" method="get">
    <div class="form-group">
        <label for="plan">Reading Plan:</label>
        <select name="plan" id="plan">
            <option value="nt">New Testament Only (~260 chapters)</option>
            <option value="ot">Old Testament Only (~929 chapters)</option>
            <option value="full">Complete Bible (~1,189 chapters)</option>
        </select>
    </div>
    
    <div class="form-group">
        <label for="chapters">Chapters per Day:</label>
        <select name="chapters" id="chapters">
            <option value="1">1 Chapter (~3-4 minutes)</option>
            <option value="2">2 Chapters (~6-8 minutes)</option>
            <option value="3">3 Chapters (~9-12 minutes)</option>
            <option value="4">4 Chapters (~12-16 minutes)</option>
            <option value="5">5 Chapters (~15-20 minutes)</option>
        </select>
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
    <p><small>⚡ <strong>Note:</strong> Text is fetched dynamically when you first access the feed, then cached for performance.</small></p>
</div>
```

</body>
</html>
"""

@app.route(’/’)
def index():
today = datetime.now().strftime(’%Y-%m-%d’)
feed_url = request.args.get(‘feed_url’)
return render_template_string(HTML_TEMPLATE, today=today, feed_url=feed_url)

@app.route(’/generate’)
def generate_feed():
plan = request.args.get(‘plan’, ‘nt’)
chapters = int(request.args.get(‘chapters’, 1))
start_date = request.args.get(‘start_date’, datetime.now().strftime(’%Y-%m-%d’))

```
feed_url = f"{request.host_url}feed/{plan}/{start_date}/{chapters}/feed.rss"
return index() + f"<script>window.history.replaceState(null, null, '/?feed_url={feed_url}');</script>"
```

@app.route(’/feed/<plan>/<start_date>/<int:chapters>/feed.rss’)
def serve_feed(plan, start_date, chapters):
try:
print(f”Generating feed: {plan}, {start_date}, {chapters} chapters/day”)
feed_content = generator.generate_rss_feed(plan, start_date, chapters)
return Response(feed_content, mimetype=‘application/rss+xml’)
except Exception as e:
print(f”Error: {e}”)
return f”Error generating feed: {str(e)}”, 400

def run_bible_rss_server():
“””

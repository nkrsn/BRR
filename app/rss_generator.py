from datetime import datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from xml.dom import minidom
from urllib.parse import quote
from flask import request
from .text_provider import BibleTextProvider

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
            ]
        }

    def get_plan(self, plan_type):
        if plan_type == 'ot':
            return self.bible_books['ot']
        elif plan_type == 'nt':
            return self.bible_books['nt']
        elif plan_type == 'full':
            return self.bible_books['ot'] + self.bible_books['nt']
        else:
            raise ValueError("Invalid plan")

    def get_chapters_for_day(self, plan_type, start_date, chapters_per_day, current_date):
        plan = self.get_plan(plan_type)
        days_elapsed = (current_date - start_date).days
        chapter_index = days_elapsed * chapters_per_day

        all_chapters = []
        for book, count in plan:
            for ch in range(1, count + 1):
                all_chapters.append((book, ch))

        return all_chapters[chapter_index:chapter_index + chapters_per_day]

    def generate_rss_feed(self, plan_type, start_date_str, chapters_per_day=1, days_to_generate=30):
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d')

        rss = Element('rss', version='2.0')
        channel = SubElement(rss, 'channel')
        SubElement(channel, 'title').text = f"Daily Bible Reading - {plan_type.upper()}"
        SubElement(channel, 'description').text = f"{chapters_per_day} chapter(s) per day from the {plan_type.upper()}."
        SubElement(channel, 'link').text = request.host_url if request else "http://localhost"
        SubElement(channel, 'language').text = "en-us"
        SubElement(channel, 'lastBuildDate').text = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S +0000')

        for day in range(days_to_generate):
            current_date = start_date + timedelta(days=day)
            chapters = self.get_chapters_for_day(plan_type, start_date, chapters_per_day, current_date)
            if not chapters:
                break

            item = SubElement(channel, 'item')
            title = f"Day {day + 1}: {', '.join([f'{b} {c}' for b, c in chapters])}"
            SubElement(item, 'title').text = title
            SubElement(item, 'guid', isPermaLink="false").text = f"{plan_type}-{start_date_str}-{day+1}"
            SubElement(item, 'pubDate').text = current_date.replace(hour=6).strftime('%a, %d %b %Y %H:%M:%S +0000')

            content = ""
            for book, ch in chapters:
                text = self.text_provider.get_chapter_text(book, ch)
                content += f"<h2>{book} {ch}</h2><pre>{text}</pre><hr/>"

            description = SubElement(item, 'description')
            description.text = f"<![CDATA[{content}]]>"

        pretty_xml = minidom.parseString(tostring(rss, 'utf-8')).toprettyxml(indent="  ")
        return pretty_xml

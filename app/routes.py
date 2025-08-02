from flask import Blueprint, render_template, request, Response
from datetime import datetime
from .rss_generator import BibleRSSGenerator

main = Blueprint("main", __name__)
generator = BibleRSSGenerator()

@main.route("/")
def index():
    today = datetime.now().strftime("%Y-%m-%d")
    feed_url = request.args.get("feed_url")
    return render_template("index.html", today=today, feed_url=feed_url)

@main.route("/generate")
def generate():
    plan = request.args.get("plan", "nt")
    start_date = request.args.get("start_date", datetime.now().strftime("%Y-%m-%d"))
    chapters = int(request.args.get("chapters", 1))
    feed_url = f"/feed/{plan}/{start_date}/{chapters}/feed.rss"
    return render_template("index.html", today=start_date, feed_url=feed_url)

@main.route("/feed/<plan>/<start_date>/<int:chapters>/feed.rss")
def serve_feed(plan, start_date, chapters):
    try:
        feed_content = generator.generate_rss_feed(plan, start_date, chapters_per_day=chapters)
        return Response(feed_content, mimetype="application/rss+xml")
    except Exception as e:
        return f"Error: {str(e)}", 400

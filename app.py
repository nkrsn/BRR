from app import create_app
import os

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
    
    
    
    
from flask import current_app

@main.route("/")
def index():
    print("CWD:", os.getcwd())
    print("Template Folder:", current_app.template_folder)
    ...

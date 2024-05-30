from pathlib import Path
from flask import Flask

TEMPLATE_FOLDER = Path("templates")
STATIC_FOLDER = Path("static")


app = Flask(
    __name__, 
    template_folder=TEMPLATE_FOLDER,
    static_folder=STATIC_FOLDER
    )

import os

MON_URI = os.environ.get('MON_URI', 'mongodb+srv://shiresalmaan0:307112@cluster0.dudjyab.mongodb.net/?retryWrites=true&w=majority')
DATABASE_NAME = os.environ.get('DATABASE_NAME', 'bookshelf_db')
DEBUG_MODE = os.environ.get('DEBUG_MODE', 'True') == 'True'

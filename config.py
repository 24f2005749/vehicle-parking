from dotenv import load_dotenv
import os

load_dotenv()

class Config:
    SQLALCHEMY_DATABASE_URI = os.getenv('SQLALCHEMY_DATABASE_URI')
    SECRET_KEY = os.getenv('SECRET_KEY')
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv('SQLALCHEMY_TRACK_MODIFICATIONS', 'False') == 'True'
    ADMIN_USERNAME=os.getenv('ADMIN_USERNAME')
    ADMIN_PASSWORD=os.getenv('ADMIN_PASSWORD')
    

print('Config loaded!')
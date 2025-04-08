class Config:
    SECRET_KEY = 'fc3e90f3c184d87568ba60c8dcddcc30'
    MYSQL_HOST = 'localhost'
    MYSQL_USER = 'root'
    MYSQL_PASSWORD = 'user@123'
    MYSQL_DB = 'TestDB'  # Default DB

class TestingConfig(Config):
    TESTING = True
    MYSQL_DB = 'test_db'  # Test-specific database

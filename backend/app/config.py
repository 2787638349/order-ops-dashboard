class Config:
    FLASK_HOST = "127.0.0.1"
    FLASK_PORT = 5000
    FLASK_DEBUG = True

    ADMIN_USERNAME = "admin"
    ADMIN_PASSWORD = "123456"
    ADMIN_TOKEN = "order-ops-admin-token"
    
    SQLALCHEMY_DATABASE_URI = (
        "mysql+pymysql://root:123456@127.0.0.1:3306/order_ops_db?charset=utf8mb4"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
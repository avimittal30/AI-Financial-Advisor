import reflex as rx
import os

class Config(rx.Config):
    pass

config = Config(
    app_name="frontend",
    db_url="sqlite:///reflex.db",
    frontend_port=3000,
    backend_port=8001,
) 

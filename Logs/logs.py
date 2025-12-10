import os
import logging


parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

db_log_file_path = os.path.join(parent_dir, 'db_logs.log')
api_log_file_path = os.path.join(parent_dir, "api_log.log")
streamlit_log_file_path = os.path.join(parent_dir,"streamlit_log.log")

LOG_FORMAT = '%(asctime)s - %(levelname)s - %(message)s'

db_logger = logging.getLogger('db_logger')
db_logger.setLevel(logging.DEBUG)


db_handler = logging.FileHandler(db_log_file_path, mode='a')
db_handler.setLevel(logging.DEBUG)
db_handler.setFormatter(logging.Formatter(LOG_FORMAT))

db_logger.addHandler(db_handler)


api_logger = logging.getLogger('api_logger')
api_logger.setLevel(logging.DEBUG)

api_handler = logging.FileHandler(api_log_file_path, mode='a')
api_handler.setLevel(logging.DEBUG)
api_handler.setFormatter(logging.Formatter(LOG_FORMAT))

api_logger.addHandler(api_handler)

streamlit_logger = logging.getLogger('streamlit_logger')
streamlit_logger.setLevel(logging.DEBUG)

streamlit_handler = logging.FileHandler(streamlit_log_file_path, mode='a')
streamlit_handler.setLevel(logging.DEBUG)
streamlit_handler.setFormatter(logging.Formatter(LOG_FORMAT))

streamlit_logger.addHandler(streamlit_handler)

import os
import logging
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
import re

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def mask_password(url):
    return re.sub(r':(.+?)@', ':***@', url)

def verify_database_connection():
    try:
        # Get the DATABASE_URL from environment variables
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            logger.error("DATABASE_URL environment variable is not set.")
            return "Error: DATABASE_URL environment variable is not set."
        
        masked_url = mask_password(database_url)
        logger.info(f"Attempting to connect to: {masked_url}")
        
        # Create a SQLAlchemy engine using the DATABASE_URL
        engine = create_engine(database_url, echo=True)
        logger.info("Engine created successfully")
        
        # Try to connect to the database
        with engine.connect() as connection:
            logger.info("Connection established, executing query")
            result = connection.execute(text("SELECT 1"))
            row = result.fetchone()
            if row and row[0] == 1:
                logger.info("Query executed successfully")
                return "Success: Database connection verified."
            else:
                logger.warning("Unexpected result from database")
                return "Error: Unexpected result from database."
    except SQLAlchemyError as e:
        logger.error(f"SQLAlchemy error: {str(e)}")
        return f"Error: Failed to connect to the database. Details: {str(e)}"
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return f"Error: An unexpected error occurred. Details: {str(e)}"

if __name__ == "__main__":
    result = verify_database_connection()
    print(result)

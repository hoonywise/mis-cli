import oracledb
import logging
import configparser
from pathlib import Path

# ==== LOGGING SETUP ====
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Update path to look in config folder
CONFIG_PATH = Path(__file__).parent.parent / "config" / "config.ini"

def read_config(section="dwh"):
    """Read database configuration from config.ini"""
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    if section not in config:
        raise ValueError(f"Section [{section}] not found in config file.")
    return (
        config[section]["username"],
        config[section]["password"],
        config[section]["dsn"]
    )

def get_oracle_client_path():
    config = configparser.ConfigParser()
    config.read(CONFIG_PATH)
    return config["oracle_client"]["path"]

def init_oracle_client():
    try:
        lib_dir = get_oracle_client_path()
        oracledb.init_oracle_client(lib_dir=lib_dir)
        logging.info(f"✅ Oracle Client Loaded from {lib_dir}")
    except oracledb.DatabaseError as e:
        logging.warning(f"⚠️ Running in Thin Mode. Error: {e}")

def get_connection(section="dwh", use_pool=False, pool_min=1, pool_max=5, pool_inc=1):
    """
    Get a direct connection or a pooled connection to Oracle using config.ini.
    
    Args:
        section (str): Config section to use. Options:
                      - "dwh" for Data Warehouse (DWHDB_DB) - used by dat_loader
                      - "prod" for Production (PROD_DB) - used by gvprmis_export
        use_pool (bool): Whether to use connection pooling
        pool_min/max/inc (int): Pool configuration parameters
    
    Returns:
        Oracle connection object or None if connection fails
    """
    user, password, dsn = read_config(section)
    init_oracle_client()
    
    if use_pool:
        try:
            pool = oracledb.create_pool(
                user=user,
                password=password,
                dsn=dsn,
                min=pool_min,
                max=pool_max,
                increment=pool_inc,
            )
            logging.info(f"✅ Connection pool created successfully for {dsn}")
            return pool.acquire()
        except oracledb.DatabaseError as e:
            logging.error(f"❌ Error creating connection pool for {dsn}: {e}")
            return None
    else:
        try:
            conn = oracledb.connect(user=user, password=password, dsn=dsn)
            logging.info(f"✅ Connected to {dsn} as {user}")
            return conn
        except oracledb.DatabaseError as e:
            logging.error(f"❌ Connection failed for {dsn}: {e}")
            return None

# Example usage:
if __name__ == "__main__":
    # Test DWH connection
    dwh_conn = get_connection("dwh")
    if dwh_conn:
        print("DWH Connection successful!")
        dwh_conn.close()
    
    # Test PROD connection  
    prod_conn = get_connection("prod")
    if prod_conn:
        print("PROD Connection successful!")
        prod_conn.close()
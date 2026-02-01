import os
import configparser
import questionary

CONFIG_PATH = os.path.join("config", "config.ini")

def prompt_config():
    print("=== MIS CLI Configuration Setup ===")
    dwh_user = questionary.text("Enter DWH username:").ask()
    dwh_pass = questionary.password("Enter DWH password:").ask()
    dwh_dsn = questionary.text("Enter DWH DSN:").ask()
    prod_user = questionary.text("Enter PROD username:").ask()
    prod_pass = questionary.password("Enter PROD password:").ask()
    prod_dsn = questionary.text("Enter PROD DSN:").ask()
    oracle_client_path = questionary.text("Enter Oracle client path:").ask()
    submission_path = questionary.text("Enter submission path:").ask()

    config = configparser.ConfigParser()
    config["dwh"] = {"username": dwh_user, "password": dwh_pass, "dsn": dwh_dsn}
    config["prod"] = {"username": prod_user, "password": prod_pass, "dsn": prod_dsn}
    config["oracle_client"] = {"path": oracle_client_path}
    config["submission"] = {"path": submission_path}

    os.makedirs("config", exist_ok=True)
    with open(CONFIG_PATH, "w") as f:
        config.write(f)
    print(f"Configuration saved to {CONFIG_PATH}")

if __name__ == "__main__":
    prompt_config()
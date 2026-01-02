import os
from datetime import datetime
import pandas as pd

# ------------------------------------------------------------------------------



def write_log(message, log_dir, config):
    # TODO: remove config and replace with file_path arg
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_path = os.path.join(log_dir, f"log_{config.identifier}.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%H%M:%S")
        file.write(f"[{timestamp}] {message}\n\n")


def log_config(log_dir, config):
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save text of gemini prompt--------
    with open(config.prompt_text_path, "r") as file:
        prompt_text = file.read()
    with open(os.path.join(log_dir, "prompt_text.txt"), "a",
              encoding="utf-8") as file:
        file.write(prompt_text)

    # Save parameter values ----------
    file_path = os.path.join(log_dir, f"log_{config.identifier}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] \n\n")
        file.write(f"CONFIG PARAMETERS\n\n")
        # file.write(f"Directory file year: {input_file_year}\n")
        file.write(f"Start page: {config.start_page}\n")
        file.write(f"End page: {config.start_page + config.n_pages - 1}\n")
        file.write(f"Page window: {config.page_window}\n")
        file.write(f"Prompt text file: {config.prompt_text_name}\n")
        file.write(f"Gemini model: {config.gemini_model_id}\n\n")

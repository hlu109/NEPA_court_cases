import os
from datetime import datetime


def write_log(message, log_dir, identifier):
    """
    Appends a timestamped message to a run-specific log file.

    Parameters:
        message (str): Message text to append.
        log_dir (str): Directory where log files are stored.
        identifier (str): Run identifier used in the log filename.
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)
    file_path = os.path.join(log_dir, f"log_{identifier}.txt")
    with open(file_path, "a", encoding="utf-8") as file:
        timestamp = datetime.now().strftime("%H%M:%S")
        file.write(f"[{timestamp}] {message}\n\n")


def _log_and_print(message, log_dir=None, identifier=None):
    """
    Convenient wrapper to print a message and optionally writes it to a log file.

    Parameters:
        message (str): Message to print and optionally log.
        log_dir (str, optional): Log directory; if omitted, message is only printed.
        identifier (str, optional): Run identifier for the log filename.
    """
    print(message)
    if log_dir and identifier:
        write_log(message, log_dir, identifier)


def log_config(prompt_text_path,
               gemini_model_id,
               identifier,
               log_dir,
               input_dir=None,
               case_ids=None):
    """
    Logs prompt text and configuration values for a Gemini run.

    Parameters:
        prompt_text_path (str): Path to the prompt text file.
        gemini_model_id (str): Gemini model to use.
        identifier (str): Run identifier used for config and log filenames.
        log_dir (str): Directory where log outputs are saved.
        input_dir (str, optional): Input directory being processed.
        case_ids (list, optional): Subset of case IDs being processed. (None value indicates all cases.)
    """
    if not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # Save text of gemini prompt--------
    with open(prompt_text_path, "r", encoding="utf-8") as file:
        prompt_text = file.read()
    with open(os.path.join(log_dir, f"prompt_text_{identifier}.txt"), "a",
              encoding="utf-8") as file:
        file.write(prompt_text)

    # Save parameter values ----------
    file_path = os.path.join(log_dir, f"log_{identifier}.txt")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with open(file_path, "a", encoding="utf-8") as file:
        file.write(f"[{timestamp}] \n\n")
        file.write(f"CONFIG PARAMETERS\n\n")
        file.write(f"Input directory: {input_dir}\n")
        file.write(f"Case IDs filter: {case_ids if case_ids else 'All cases'}\n")
        file.write(f"Prompt text file: {prompt_text_path}\n")
        file.write(f"Gemini model: {gemini_model_id}\n\n")

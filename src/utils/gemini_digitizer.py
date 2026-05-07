from pydantic import BaseModel
import time
import requests
import os
import json
import pandas as pd
from utils.gemini_logging import _log_and_print


def upload_to_API(genai_client,
                  file_path: str,
                  log_dir=None,
                  identifier=None):
    """
    Uploads court case opinion file to the Gemini API.

    Parameters:
        genai_client: Gemini API client.
        file_path (str): Path to the input opinion file.
        log_dir (str, optional): Directory for writing Gemini error logs.
        identifier (str, optional): Run identifier used for the Gemini log filename.

    Returns:
        object: Uploaded file object from the Gemini API.
    """
    file_name = os.path.basename(file_path)

    # Check if file already exists in the File API
    uploaded_file = None
    max_retries = 7
    base_wait = 10
    should_check_existing = True

    # Error handling: for 503 errors (server side), retry with expotential backoff/wait time. 
    # For all other errors, in order to keep things running, we bypass the check for existing files and upload directly.
    for attempt in range(max_retries):
        if not should_check_existing:
            break
        try:
            existing_files = genai_client.files.list()
            for f in existing_files:
                if f.display_name == file_name:
                    uploaded_file = f
                    print(
                        f"    File '{file_name}' already exists in the File API. Skipping upload."
                    )
                    break
            break
        except Exception as e:
            if '503' in str(e):
                wait_time = base_wait * (2**attempt)
                m = f"Error 503 while checking existing upload for '{file_name}' on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
                _log_and_print(m, log_dir, identifier)
                time.sleep(wait_time)
            else:
                m = f"Warning: existing file check failed for '{file_name}'. Skipping check and proceeding with direct upload: {e}"
                _log_and_print(m, log_dir, identifier)
                should_check_existing = False

    if should_check_existing and not uploaded_file and attempt == max_retries - 1:
        m = f"Max 503 retries reached while checking existing upload for '{file_name}'. Proceeding with direct upload."
        _log_and_print(m, log_dir, identifier)

    # Upload file (only if it has not already been uploaded)
    if not uploaded_file:
        print(f"    Uploading file: {file_name}")
        uploaded_file = genai_client.files.upload(
            file=file_path, config={'display_name': file_name})

    return uploaded_file


def extract_case_data(genai_client,
                      input_file,
                      data_struct: BaseModel,
                      prompt_text: str,
                      model_id: str,
                      case_id=None,
                      log_dir=None,
                      identifier=None,
                      debug=False):
    """
    Extracts structured data from a court case opinion file using the Gemini API.

    Parameters:
        genai_client: Gemini API client.
        input_file: File object uploaded to the Gemini API.
        data_struct (BaseModel): Data structure for extracted content.
        prompt_text (str): Prompt text for the API.
        model_id (str): Gemini model ID.
        case_id (str, optional): Opinion/case identifier used in error logging context.
        log_dir (str, optional): Directory for writing Gemini error logs.
        identifier (str, optional): Run identifier used for the Gemini log filename.
        debug (bool): Enables debug logging.

    Returns:
        dict or None: Parsed structured data if successful, otherwise None.
    """
    # limit output size
    max_token_output = 80000
    max_retries = 7
    base_wait = 10  # this is in seconds!

    for attempt in range(max_retries):
        print(f"      Attempt {attempt + 1} to extract data...")
        try:
            # Generate a structured response using the Gemini API ---
            response = genai_client.models.generate_content(
                model=model_id,
                contents=[prompt_text, input_file],
                config={
                    'response_mime_type': 'application/json',
                    'response_schema': data_struct,
                    'max_output_tokens': max_token_output
                })

            # print("API Response:", response)  # Debugging step
            # print(" Response Usage Metadata:", response.usage_metadata)

            # Added: Check for token limit issues
            if hasattr(response, 'candidates') and response.candidates:
                if response.candidates[0].finish_reason.name == 'MAX_TOKENS':
                    print(
                        f"WARNING: Response truncated due to token limit. Consider increasing max_output_tokens or splitting the page."
                    )
                    print(
                        f"Token count: {response.usage_metadata.candidates_token_count}"
                    )

            if debug:
                file_path = "output.txt"

                # Open the file in append mode and write text multiple times
                with open(file_path, "a", encoding="utf-8") as file:
                    for i in range(5):  # Writing 5 times
                        file.write(
                            f"Line {i + 1}: This is some text being written.\n"
                        )

            if not response or not response.parsed:
                m = "ERROR: The API did not return a valid parsed response."
                _log_and_print(
                    f"case_id={case_id} \t\nmodel_id={model_id} \t\nextract_attempt={attempt + 1} \t\n{m}",
                    log_dir, identifier)
                return None

            return response.parsed

        # Add in a wait time response if the model is temporarily unavailable (error 503)
        # TODO: add wait time to handle rate limit errors
        except Exception as e:
            if '503' in str(e):
                wait_time = base_wait * (2**attempt)
                m = f"Error 503 on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
                _log_and_print(
                    f"case_id={case_id} \t\nmodel_id={model_id} \t\nextract_attempt={attempt + 1} \t\n{m}",
                    log_dir, identifier)
                time.sleep(wait_time)
            else:
                m = f"EXCEPTION occurred (non-retryable): {e}"
                _log_and_print(
                    f"case_id={case_id} \t\nmodel_id={model_id} \t\nextract_attempt={attempt + 1} \t\n{m}",
                    log_dir, identifier)
                return None

    m = "Max 503 error retries reached. Giving up on this page."
    _log_and_print(
        f"case_id={case_id} \t\nmodel_id={model_id} \t\n{m}",
        log_dir, identifier)
    return None


def process_cases(genai_client,
                  input_dir: str,
                  data_struct: BaseModel,
                  prompt_text: str,
                  model_id: str,
                  outfile_path: str,
                  intermediate_dir: str,
                  to_dataframe_fn,
                  file_extension: str = "html",
                  case_ids: list = None,
                  log_dir=None,
                  identifier=None,
                  debug=False):
    """
    Extracts structured data from court case opinion files and saves results.

    Parameters:
        genai_client: Gemini API client.
        input_dir (str): Path to directory containing opinion_XXX folders.
        data_struct (BaseModel): Data structure for extracted content.
        prompt_text (str): Prompt text for the API.
        model_id (str): Gemini model ID.
        outfile_path (str): Path to save extracted data.
        intermediate_dir (str): Folder for intermediate outputs.
        to_dataframe_fn: Function converting parsed schema object to dataframe.
        file_extension (str): Opinion file extension inside each opinion_XXX folder ("html" or "pdf").
        case_ids (list): Optional list of specific case IDs to process. If None, processes all cases.
        log_dir (str, optional): Directory for writing Gemini error logs.
        identifier (str, optional): Run identifier used for the Gemini log filename.
        debug (bool): Enables debug logging.

    Returns:
        pd.DataFrame: Aggregated structured data extracted from all cases.
    """
    # TODO: add handling if there are errors for one page but not other pages
    # include a print and a log of failed pages

    # Get list of case folders to process
    if case_ids is None:
        case_folders = [
            f for f in os.listdir(input_dir) if f.startswith('opinion_')
            and os.path.isdir(os.path.join(input_dir, f))
        ]
        case_ids = [f.replace('opinion_', '') for f in case_folders]
    total_cases = len(case_ids)

    all_dataframes = []
    max_retries = 5
    start_time = time.time()

    # track issues in real time 
    error_count = 0
    missing_file_skip_count = 0

    for i, case_id in enumerate(case_ids):
        # add counter for cases processed
        print(f"\nProcessing case {case_id} ({i + 1}/{total_cases})...")
        case_folder = os.path.join(input_dir, f"opinion_{case_id}")
        opinion_path = os.path.join(case_folder, f"opinion_{case_id}.{file_extension}")
        file_source_indicator = ""

        # Check if opinion file exists
        if not os.path.exists(opinion_path):
            if file_extension == "pdf":
                fallback_html_path = os.path.join(case_folder, f"opinion_{case_id}.html")
                if os.path.exists(fallback_html_path):
                    print(
                        f"WARNING: .pdf file not found for case {case_id}; using .html fallback."
                    )
                    opinion_path = fallback_html_path
                    file_source_indicator = "pdf not found, html used"
                else:
                    print(
                        f"WARNING: .pdf file not found for case {case_id}, and .html fallback also missing; skipping..."
                    )
                    file_source_indicator = "pdf not found, html not found"
                    missing_file_skip_count += 1
                    continue
            else:
                print(
                    f"WARNING: .{file_extension} file not found for case {case_id}, skipping..."
                )
                missing_file_skip_count += 1
                continue
        elif file_extension == "pdf":
            file_source_indicator = "pdf used"

        retries = 0
        success = False
        prompt = prompt_text
        df = None

        while retries < max_retries and not success:
            try:
                print(f"\t(Attempt {retries + 1})...")

                # Upload opinion file
                uploaded_file = upload_to_API(genai_client,
                                              opinion_path,
                                              log_dir=log_dir,
                                              identifier=identifier)

                # Extract case data
                result = extract_case_data(genai_client, uploaded_file,
                                           data_struct, prompt, model_id,
                                           case_id=case_id,
                                           log_dir=log_dir,
                                           identifier=identifier,
                                           debug=debug)

                if result:
                    success = True
                    runtime_metadata = {
                        "opinion_id": case_id,
                        "file_source_indicator": file_source_indicator,
                        "model_id": model_id
                    }

                    # add additional tracked information to the json 
                    json_path = os.path.join(intermediate_dir,
                                             f"coded_opinion_{case_id}.json")
                    result_json = result.model_dump()
                    result_json.update(runtime_metadata)

                    # save intermediate data structure to json
                    # (for the future - to handle unplanned termination and be able to resume from existing progress)
                    with open(json_path, "w", encoding="utf-8") as file:
                        json.dump(result_json, file, indent=4, ensure_ascii=False)
                    print(
                        f"  Saved intermediate JSON of coded opinion to {json_path}"
                    )

                    df = to_dataframe_fn(result)
                    # add metadata to final dataframe
                    for key, value in runtime_metadata.items():
                        df[key] = value

                    # Immediately delete the uploaded file to avoid storage limits
                    try:
                        genai_client.files.delete(name=uploaded_file.name)
                        print(f"Deleted uploaded file: {uploaded_file.name}")
                    except Exception as e:
                        print(
                            f"Warning: failed to delete uploaded file {uploaded_file.name}: {e}"
                        )

                else:
                    m = f"FAILURE - No data found for case {case_id}."
                    _log_and_print(
                        f"case_id={case_id} \t\nfile_source_indicator={file_source_indicator} \t\nmodel_id={model_id} \t\n{m}",
                        log_dir, identifier)

            except requests.exceptions.ConnectionError as e:
                m = f"Connection error for opinion {case_id}: {e}"
                _log_and_print(
                    f"case_id={case_id} \t\ncase_attempt={retries + 1} \t\nfile_source_indicator={file_source_indicator} \t\n{m}",
                    log_dir, identifier)
                retries += 1
                if retries < max_retries:
                    m = f"Retrying opinion {case_id} in 5 seconds..."
                    _log_and_print(
                        f"case_id={case_id} \t\ncase_attempt={retries + 1} \t\n{m}",
                        log_dir, identifier)
                    time.sleep(5)
                else:
                    _log_and_print(
                        f"Max retries reached for case {case_id}. Raising ValueError.",
                        log_dir, identifier)
                    print(f"Warning: Max retries reached for case {case_id}.")
               

            # TODO: add error handling for other errors
            # (EXCEPTION occurred (non-retryable): 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details.', 'status': 'RESOURCE_EXHAUSTED'}}
            # rate limits are per minute and per day. first try to wait a minute, if that doesn't work, then wait until the end of the day (compute how much time left). 
            # it would be good to also send an email... if we hit the day rate limit then we screwed up and should downgrade to a lower model 

        if not success:
            error_count += 1
            # continue

        # Combine output
        if success and df is not None:
            all_dataframes.append(df)

        total_time_elapsed = time.time() - start_time
        avg_time_per_case = total_time_elapsed / (i + 1)
        print(f"Total time elapsed: {total_time_elapsed / 3600:.2f} hrs")
        print(f"Average time per case so far: {avg_time_per_case:.2f} s")
        print(f"Cases with no Gemini output so far: {error_count}")
        print(f"Cases skipped for missing files so far: {missing_file_skip_count}")

    # log error and missing file counts to log file 
    m = f"Total cases with no Gemini output: {error_count}"
    _log_and_print(m, log_dir, identifier)
    m = f"Total cases skipped for missing files: {missing_file_skip_count}"
    _log_and_print(m, log_dir, identifier)

    if all_dataframes:
        final_dataframe = pd.concat(all_dataframes, ignore_index=True)
        print(f"\n Generated dataframe with {final_dataframe.shape[0]} rows")
        final_dataframe.to_csv(outfile_path, index=False)
        print(f"  Saved final output to {outfile_path}\n")
        return final_dataframe
    else:
        return None

from pydantic import BaseModel
import time
import requests
import os
import pandas as pd


def upload_to_API(genai_client, file_path: str):
    """
    Uploads HTML court case opinion to the Gemini API.

    Parameters:
        genai_client: Gemini API client.
        file_path (str): Path to the input HTML file.

    Returns:
        object: Uploaded file object from the Gemini API.
    """
    file_name = os.path.basename(file_path)

    # Check if file already exists in the File API
    existing_files = genai_client.files.list()
    uploaded_file = None
    for f in existing_files:
        if f.display_name == file_name:
            uploaded_file = f
            print(
                f"    File '{file_name}' already exists in the File API. Skipping upload."
            )
            break

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
                      debug=False):
    """
    Extracts structured data from a court case HTML using the Gemini API.

    Parameters:
        genai_client: Gemini API client.
        input_file: File object uploaded to the Gemini API.
        data_struct (BaseModel): Data structure for extracted content.
        prompt_text (str): Prompt text for the API.
        model_id (str): Gemini model ID.
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
                print("ERROR: The API did not return a valid parsed response.")
                return None

            return response.parsed

        # Add in a wait time response if the model is temporarily unavailable (error 503)
        # TODO: add wait time to handle rate limit errors
        except Exception as e:
            if '503' in str(e):
                wait_time = base_wait * (2**attempt)
                print(
                    f"Error 503 on attempt {attempt + 1}. Retrying in {wait_time:.1f}s..."
                )
                time.sleep(wait_time)
            else:
                print(f"EXCEPTION occurred (non-retryable): {e}")
                return None

    print("Max 503 error retries reached. Giving up on this page.")
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
        file_extension (str): Opinion file extension inside each opinion_XXX folder (for example, "html" or "pdf").
        case_ids (list): Optional list of specific case IDs to process. If None, processes all cases.
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

    for i, case_id in enumerate(case_ids):
        # add counter for cases processed
        print(f"\nProcessing case {case_id} ({i + 1}/{total_cases})...")
        case_folder = os.path.join(input_dir, f"opinion_{case_id}")
        opinion_path = os.path.join(case_folder, f"opinion_{case_id}.{file_extension}")

        # Check if opinion file exists
        if not os.path.exists(opinion_path):
            print(
                f"WARNING: .{file_extension} file not found for case {case_id}, skipping..."
            )
            continue

        retries = 0
        success = False
        prompt = prompt_text
        df = None

        while retries < max_retries and not success:
            try:
                print(f"\t(Attempt {retries + 1})...")

                # Upload opinion file
                uploaded_file = upload_to_API(genai_client, opinion_path)

                # Extract case data
                result = extract_case_data(genai_client, uploaded_file,
                                           data_struct, prompt, model_id,
                                           debug)
                success = True

                if result:
                    # save intermediate data structure to json
                    json_path = os.path.join(intermediate_dir,
                                             f"coded_opinion_{case_id}.json")
                    result.save_json(json_path)
                    print(
                        f"  Saved intermediate JSON of coded opinion to {json_path}"
                    )

                    df = to_dataframe_fn(result)
                    df["opinion_id"] = case_id
                    df["model_id"] = model_id

                    # Immediately delete the uploaded file to avoid storage limits
                    try:
                        genai_client.files.delete(name=uploaded_file.name)
                        print(f"Deleted uploaded file: {uploaded_file.name}")
                    except Exception as e:
                        print(
                            f"Warning: failed to delete uploaded file {uploaded_file.name}: {e}"
                        )

                else:
                    print(f"FAILURE - No data found for case {case_id}.")

            except requests.exceptions.ConnectionError as e:
                print(f"Connection error for opinion {case_id}: {e}")
                retries += 1
                if retries < max_retries:
                    print(f"Retrying opinion {case_id} in 5 seconds...")
                    time.sleep(5)
                else:
                    raise ValueError(f"Max retries reached for case {case_id}")

            # TODO: add error handling for other errors
            # (EXCEPTION occurred (non-retryable): 429 RESOURCE_EXHAUSTED. {'error': {'code': 429, 'message': 'Resource exhausted. Please try again later. Please refer to https://cloud.google.com/vertex-ai/generative-ai/docs/error-code-429 for more details.', 'status': 'RESOURCE_EXHAUSTED'}}

        # Combine output
        if df is not None:
            all_dataframes.append(df)

        total_time_elapsed = time.time() - start_time
        avg_time_per_case = total_time_elapsed / (i + 1)
        print(f"Total time elapsed: {total_time_elapsed:.2f}s")
        print(f"Average time per case so far: {avg_time_per_case:.2f}s")

    if all_dataframes:
        final_dataframe = pd.concat(all_dataframes, ignore_index=True)
        print(f"\n Generated dataframe with {final_dataframe.shape[0]} rows")
        final_dataframe.to_csv(outfile_path, index=False)
        print(f"  Saved final output to {outfile_path}\n")
        return final_dataframe
    else:
        return None

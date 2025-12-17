# NEPA Court Cases
# This script downloads court cases via the CourtListener API
# Hannah Lu
# hannah.lu@yale.edu

# ------------------------------------------------------------------------------
# Setup 
# ------------------------------------------------------------------------------
# install.packages("httr")
# install.packages("jsonlite")

library(httr)
library(jsonlite)
library(dplyr)
library(units)

options(warn = 1) # set warnings to print as they occur

BASE_DIR <- getwd()
DATA_DIR <- file.path(base_dir, "data")


script_start_time <- Sys.time()
# ------------------------------------------------------------------------------
timestamp <- format(Sys.time(), "%Y%m%d_%H%M%S")
setup_directories <- function(data_dir = DATA_DIR) {
  
  dirs <- c(
    data_dir,
    file.path(data_dir, "metadata"),
    file.path(data_dir, "opinions", "text"),
    file.path(data_dir, "opinions", "pdf"),
    file.path(data_dir, "logs")
  )
  
  for (dir in dirs) {
    if (!dir.exists(dir)) {
      dir.create(dir, recursive = TRUE)
      message("Created directory: ", dir)
    }
  }
}

exit()
# ------------------------------------------------------------------------------
# load API key (read from text file)
API_key_path <- "secret/courtlistener_apikey.txt"
API_KEY <- readLines(API_key_path)
print("API key loaded.")

# API query
BASE_URL <- "https://www.courtlistener.com/api/rest/v4/"

courtlistener_search <- function(
  query_text, result_type, max_pages = 450, api_key = API_KEY) {
  ## Make a request to the CourtListener search API.
  ##
  ## Args:
  ##   query_text: The search query string.
  ##   result_type: The type of results to return. The options are: 
  ##      * "o":  Case law opinion clusters with nested Opinion documents.
  ##      * "r":  List of Federal cases (dockets) with up to three nested 
  ##              documents.
  ##      * "rd": Federal filing documents from PACER.
  ##      * "d":  Federal cases (dockets) from PACER.
  ##      * "p":  Judges.
  ##      * "oa":  Oral argument audio files.
  ##   api_key: The API key for authentication.
  ##
  ## Returns:
  ##   A list of search results.
  ##
  all_results <- list()
  endpoint <- paste0(BASE_URL, "search/")
  
  # TODO later: change for loop to while loop that ends when no more next page is available
  for (page in 1:max_pages) {
    # Set up query parameters
    params <- list(
      q = query_text, # search query
      type = result_type,
      format = "json",
      page = page
    )
    
    # Make the API request
    response <- GET(
      url = endpoint,
      query = params,
      add_headers(Authorization = paste("Token", api_key))
    )
    print(paste("request URL:", response$url))

    # Check if request was successful
    if (status_code(response) == 200) {
      content <- content(response, as = "text", encoding = "UTF-8")
      results <- fromJSON(content)
      all_results[[page]] <- results$results

      # Stop if no more results
      if (is.null(results$`next`)) {
        message(paste("No more results beyond page ", page, ". Stopping."))
        break
      }
      
    } else {
      warning(paste("Page", page, "failed with status:", status_code(response)))
      break
    }
    
    # add a small delay for the API
    Sys.sleep(0.5)
  }
  print(paste("Total number of results in search:", results$count))

  # Combine all results into one dataframe
  combined <- bind_rows(all_results)

  print(paste("Total pages retrieved:", dim(combined)[1]))
  print(colnames(all_results[[1]]))
  return(combined)
}

# get results -----------------------------

# all opinions containing "national environmental policy act"
results <- courtlistener_search("\"national environmental policy act\"", "o")
# print(results$count)
# # print(results$results) # first page of results 

# results_df <- results$results 
# print(colnames(results_df))


# ------------------------------------------------------------------------------
script_end_time <- Sys.time()
script_duration <- script_end_time - script_start_time
message(paste("time taken for script:", script_duration, units(script_duration)))

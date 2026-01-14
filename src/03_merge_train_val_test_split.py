""" This script merges the following data: 
* Maps the coding of the lead opinion to each case/cluster 
* Merges AdelGlicks data with CourtListener data using docket number and court 
* Assignment of train/val/test split 
    - all the CourtListener data that can't be matched to AdelGlicks data will be assigned to the train set 
    - AdelGlicks data that can't be matched to CourtListener data will be ignored for now with a separate flag 
    - remaining AdelGlicks data matched to CourtListener will be split 50/50 between train and val set (since there are 334 cases in AdelGlicks prior to dropping cases that can't be matched to CourtListener, we will hopefully have at least 100 cases in each of the val and test sets)


Separately, we should also standardize the variables: 
(pull from git stash files)
- court, year filed, outcome coding, etc 

Output: 
- csv with the following data: 
    - courtlistener cluster id 
    - courtlistener docket number 
    - courtlistener court 
    - adelglicks docket number
    - adelglicks court 
    - match or no match indicator 
    - train/val/test assignment 

Then split into 3 subset csvs, one each for the train, val, and test sets  
"""

def main():
    pass

if __name__ == "__main__":
    main()
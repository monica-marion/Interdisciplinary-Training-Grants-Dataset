# GENERAL INFORMATION
Repository for The NSF interdisciplinary training grants dataset

## Author/Principal Investigator Information
Name: Stasa Milojevic
Institution: Indiana University
Email: smiloj@iu.edu

## Author/Associate or Co-investigator Information
Name: Monica Marion
ORCID: 0009-0006-5115-1361
Institution: Indiana University
Email: monmmari@iu.edu

### PIPELINE FOR DATA PROCESSING

## 0_outcome_report_webscraper.py
Used to add outcome report text where available, using the python Selenium package to load each webpage, in order to load the outcome report text from javascript, and then retrieve that text by searching for the div id “porContent.”  
Input:  
	Awards.csv file downloaded from NSF  
Output:  
	grants_0.csv  

## 1a1_generate_field_list_manual.py
Cycles through the text of each grant abstract and asks for user input for each sentence with the word “from” to generate a list of sentences that are relevant to naming disciplines for that grant. It also creates a second column with automatically extracted sentence fragments from each abstract, using regex to search for the following phrases: 'domain experts in”, “department,” “combine,” “students,” “field,” “trainee,” and “disciplin-.”   
Input:  
	grants_0.csv output from the previous script  
Output:  
	grants_1.csv  
	
## MANUAL STEP: fill in the “disciplines_manual” column in grants_1.csv_
	
## 1a2_generate_field_list_manual.py
Takes the manually generated terms from each grant and creates a master list for further coding.   
Input:  
	grants_1.csv as input, but only after manual input to fill the “disciplines_manual” column,   
Output:  
	discipline_terms_manual.csv  

## 1b_generate_field_list_llm.py
Uses Ollama prompts to extract discipline terms from abstract text.   
Input:  
	grants_1.csv  
Output:  
	updated grants_1.csv  
	discipline_terms_llm.csv  

## MANUAL STEP: have both discipline_terms_manual.csv and discipline_terms_llm.csv assigned categories by two independent raters, and then create a "consensus" categories column in each table

## 1c_generate_field_list_final.py
Combines the llm generated and the manually generated lists, once they have been manually checked and a consensus list of discipline categories has been added to each.   
Input:  
	discipline_terms_manual.csv  
	discipline_terms_llm.csv  
Output:  
	discipline_terms.csv  
	
## 2_terms_extract.py
Uses the spaCy matcher to extract disciplines, Lightcast skills, and educational program terms from grant abstracts and outcome reports, and also to convert those discipline terms into broader categories.   
Input:  
	grants_0.csv  
	discipline_terms.csv  
	program_terms.csv  
	lightcast.csv  
	wos_terms.csv  
	wos_categories.csv  
	steamb_terms.csv   
Output:  
	grants.csv  

## 3_onet_match.py
Uses SBERT to build an embedding space of O*Net skills which sentences in abstracts are compared to, to generate skill matches for grants.   
Input:  
	Content Model Reference.xlsx  
	grants.csv  
Output:  
	final, updated grants.csv  
	onet_matching.csv

## 4_grant_papers_compile.R
Combines awards data with three tables from the SciSciNet data lake to produce a table of related publications.  
Input:  
	SciSciNet_NSF_Link.tsv  
	SciSciNet_Papers.tsv  
	SciSciNet_PaperDetails.tsv  
Output:  
	grant_papers.csv  


###script to extract terms from abstracts and outcome reports
#extracts discipline terms, Lightcast skills, and educational program terms
#takes as input grants_0.csv, as well as discipline_terms, program_terms, lightcast, wos_terms, wos_categories, and sedamb_terms.csv
# produces grants.csv

import re
import pandas as pd
import spacy
from spacy.matcher import PhraseMatcher
from spacy.matcher import Matcher
nlp = spacy.load("en_core_web_sm")

print ('importing')
###import data
##grant data
nsf_df = pd.read_csv("../output/grants_0.csv")

##create full address field
nsf_df['Full Address'] = nsf_df['OrganizationStreet'] + ', ' +nsf_df['OrganizationCity'] + ', ' +nsf_df['OrganizationState'] + ', ' +nsf_df['OrganizationZip']

##discipline terms list
#lists generated from 1a and 1b scripts, 
#then combined and with 'categories' categories column added manually
#through process of two-rater consensus
disc_df = pd.read_csv("../output/discipline_terms.csv")

##program terms list
program_df = pd.read_csv("../input/program_terms.csv")

## lightcast skills list 
bg_df = pd.read_csv("../input/lightcast.csv")

## Web of Science discipline categories and crosswalk
#wos categories for discipline terms
wos_df = pd.read_csv("../input/disciplinebroadarea_terms.csv")
#wos crosswalk from narrow to broad categories
wos_xwalk = pd.read_csv("../input/wos_mapped_areas.csv")

## SEDAMB categories list
sedamb_df = pd.read_csv("../input/sedamb_terms.csv")

##create function to remove disciplines contained within other disciplines
def Remove_Subset(List):
    ListCopy=List
    for Element1 in List:
        for Element2 in List:
            if (Element2 in Element1) and (Element1!= Element2):
                ListCopy.remove(Element2)
    return(ListCopy)

print ('extracting disciplines')
###extract disciplines
#make list of discipline terms
terms_list = disc_df['terms'].tolist()

#convert terms to string
for i in range(len(terms_list)):
    terms_list[i] = str(terms_list[i])

#make spacy matcher out of terms list
matcher = PhraseMatcher(nlp.vocab, attr="LOWER")
patterns = [nlp.make_doc(name) for name in terms_list]

matcher.add("Names", patterns)

## go through abstract sentences and use matcher to pull out discipline terms
nsf_df['fields_raw'] = ['none']*len(nsf_df)

for row in range(0,len(nsf_df)):
    #empty the list
    discipline_list=[]
    #set abstract
    abstract = str(nsf_df.loc[row, 'Abstract']).lower()
    #if abstract:
    if not pd.isna(abstract):
        #remove 'National Science Foundation'
        abstract = re.sub('National Science Foundation','',abstract)

        #regexreplace sciences > science
        abstract = re.sub('sciences','science',abstract)
    
        doc = nlp(abstract)
        for match_id, start, end in matcher(doc):
            #append to list
            discipline_list.append(str(doc[start:end]))
            
        #remove repeats
        discipline_list=list(set(discipline_list))
        
        #remove terms containted within other terms
        discipline_list = Remove_Subset(discipline_list)
    
        #remove punctuation
        disc_col = str(discipline_list)
        disc_col = re.sub('\[','',disc_col)
        disc_col = re.sub('\]','',disc_col)
        disc_col = re.sub('\'','',disc_col)
    else:
        disc_col=""

    #add this row to df
    nsf_df.loc[row, 'fields_raw'] = disc_col

## repeat for outcome reports
nsf_df['por_fields_raw'] = ['none']*len(nsf_df)

for row in range(0,len(nsf_df)):
    #empty the list
    discipline_list=[]
    #set abstract
    abstract = str(nsf_df.loc[row, 'Outcome Report']).lower()
    #if abstract:
    if not pd.isna(abstract):
        #regexreplace sciences > science
        abstract = re.sub('sciences','science',abstract)
    
        doc = nlp(abstract)
        for match_id, start, end in matcher(doc):
            #append to list
            discipline_list.append(str(doc[start:end]))
            
        #remove repeats
        discipline_list=list(set(discipline_list))
        
        #remove terms containted within other terms
        discipline_list = Remove_Subset(discipline_list)
    
        #remove punctuation
        disc_col = str(discipline_list)
        disc_col = re.sub('\[','',disc_col)
        disc_col = re.sub('\]','',disc_col)
        disc_col = re.sub('\'','',disc_col)
    else:
        disc_col=""

    #add this row to df
    nsf_df.loc[row, 'por_fields_raw'] = disc_col

## convert terms extracted from the text into corrected discipline terms 
# using the 'consensus' column 
# (e.g. 'computational science'>'computer science' or 'biological and computational engineering'> 'biological engineering, computational engineering')

print ('correcting discipline terms')
##define replace function
def field_replace(String):
    #split string into terms
    String_terms = String.split(', ')
    cat_list = []
    for term in String_terms:
        try:
            category=disc_df.loc[disc_df['terms'] == term]["categories"].item()
            cat_list.append(category)
        # StringCopy = re.sub(term, category, StringCopy)
        except:
            category=disc_df.loc[disc_df['terms'] == term]["categories"].tolist()
            cat_list.append(category)

    #remove empty strings
    cat_list = [s for s in cat_list if s != ""]
        
    #remove puncuation
    NewString = str(cat_list)
    NewString = NewString.replace('[], ', '') 
    NewString = re.sub('\[','',NewString)
    NewString = re.sub('\]','',NewString)
    NewString = re.sub('\'','',NewString)

    #remove duplicates
    NewString = ", ".join(set(NewString.split(", ")))

    return(NewString)

##set new column in df
nsf_df['Disciplines'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'fields_raw']
    if disc != 'none':
        new_fields = field_replace(disc)

        #then set that as the new value
        nsf_df.loc[row, 'Disciplines'] = str(new_fields)

## Repeat for Outcome reports
##set new column in df
nsf_df['Disciplines Outcome Reports'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'por_fields_raw']
    if disc != 'none':
        new_fields = field_replace(disc)

        #then set that as the new value
        nsf_df.loc[row, 'Disciplines Outcome Reports'] = str(new_fields)

###add discipline broad categories- Web of Science categories
print ('extracting DisciplineBroadArea categories')

## add WoS categories (narrow)
wos_func_df = wos_df[['terms', 'DisciplineBroadArea']]

#rename columns
wos_func_df = wos_func_df.rename(columns={'DisciplineBroadArea': 'categories'})

##define replace function
def wos_replace(String):
    #split string into terms
    String_terms = String.split(', ')
    cat_list = []
    for term in String_terms:    
        series_bool = wos_func_df['terms'] == term    
        if series_bool.any():
            try:
                category = wos_func_df.loc[wos_func_df['terms'] == term]["categories"].item()
                category = category.strip()
                cat_list.append(category)
            except:
                category=wos_func_df.loc[wos_func_df['terms'] == term]["categories"].tolist()
                cat_list.append(category)
        
    #remove puncuation
    NewString = str(cat_list)
    NewString = re.sub('\[','',NewString)
    NewString = re.sub('\]','',NewString)
    NewString = re.sub('\'','',NewString)

    #remove duplicates
    NewString = ", ".join(set(NewString.split(", ")))

    return(NewString)

##set new column in df
nsf_df['WoS Categories'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'Disciplines']
    if disc != 'none':
        new_fields = wos_replace(disc)
        #then set that as the new value
        if new_fields != 'nan':
            nsf_df.loc[row, 'WoS Categories'] = str(new_fields)

###repeat for outcome reports
##set new column in df
nsf_df['WoS Categories Outcome Reports'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'Disciplines Outcome Reports']
    if disc != 'none':
        new_fields = wos_replace(disc)
        #then set that as the new value
        if new_fields != 'nan':
            nsf_df.loc[row, 'WoS Categories Outcome Reports'] = str(new_fields)

###set broad categories (what we actually want)
#rename columns
wos_xwalk = wos_xwalk.rename(columns={'WoS subject category': 'terms', 'Broad area': 'categories'})

##fix unbreakable space characters
wos_xwalk['terms'] = wos_xwalk['terms'].str.replace(r'\s', ' ', regex=True)
wos_xwalk['terms'] = wos_xwalk['terms'].str.rstrip()

wos_xwalk['categories'] = wos_xwalk['categories'].str.replace(r'\s', ' ', regex=True)
wos_xwalk['categories'] = wos_xwalk['categories'].str.rstrip()

##define replace function
def wosx_replace(String):
    #split string into terms
    String_terms = String.split(', ')
    cat_list = []
    for term in String_terms:
        series_bool = wos_xwalk['terms'] == term    
        if series_bool.any():
            try:
                category=wos_xwalk.loc[wos_xwalk['terms'] == term]["categories"].item()
                cat_list.append(category)
            except:
                category=wos_xwalk.loc[wos_xwalk['terms'] == term]["categories"].tolist()
                cat_list.append(category)

    #remove puncuation
    NewString = str(cat_list)
    NewString = re.sub('\[','',NewString)
    NewString = re.sub('\]','',NewString)
    NewString = re.sub('\'','',NewString)

    #remove duplicates
    NewString = ", ".join(set(NewString.split(", ")))

    return(NewString)

##set new column in df
nsf_df['DisciplineBroadArea'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'WoS Categories']
    if disc != 'none':
        new_fields = wosx_replace(disc)

        #then set that as the new value
        nsf_df.loc[row, 'DisciplineBroadArea'] = str(new_fields)

## repeat for outcome reports
##set new column in df
nsf_df['DisciplineBroadArea Outcome Reports'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'WoS Categories Outcome Reports']
    if disc != 'none':
        new_fields = wosx_replace(disc)

        #then set that as the new value
        nsf_df.loc[row, 'DisciplineBroadArea Outcome Reports'] = str(new_fields)

### add discipline categories- SEDAMB
print ('extracting SEDAMB categories')

sedamb_func_df = sedamb_df[['consensus categories', 'broad categories']]

#remove all terms entries with more than one term in them by removing all rows where string contains a comma
sedamb_func_df = sedamb_func_df[~sedamb_func_df['consensus categories'].str.contains(',', na=False)]

#rename columns
sedamb_func_df = sedamb_func_df.rename(columns={'consensus categories': 'terms', 'broad categories': 'categories'})

##define replace function
def sedamb_replace(String):
    #split string into terms
    String_terms = String.split(', ')
    cat_list = []
    for term in String_terms:    
        series_bool = sedamb_func_df['terms'] == term    
        if series_bool.any():
            try:
                category=sedamb_func_df.loc[sedamb_func_df['terms'] == term]["categories"].item()
                cat_list.append(category)
            except:
                category=sedamb_func_df.loc[sedamb_func_df['terms'] == term]["categories"].tolist()
                cat_list.append(category)
     
    #remove puncuation
    NewString = str(cat_list)
    NewString = re.sub('\[','',NewString)
    NewString = re.sub('\]','',NewString)
    NewString = re.sub('\'','',NewString)

    #remove duplicates
    NewString = ", ".join(set(NewString.split(", ")))

    return(NewString)

##set new column in df
nsf_df['SEDAMB Categories'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'Disciplines']
    if disc != 'none':
        new_fields = sedamb_replace(disc)

        #then set that as the new value
        nsf_df.loc[row, 'SEDAMB Categories'] = str(new_fields)

## repeat for outcome reports
##set new column in df
nsf_df['SEDAMB Categories Outcome Reports'] = ['none']*len(nsf_df)

##iterate input terms and replace
for row in range(0,len(nsf_df)):
    #run replace on the string of the row
    disc = nsf_df.loc[row, 'Disciplines Outcome Reports']
    if disc != 'none':
        new_fields = sedamb_replace(disc)

        #then set that as the new value
        nsf_df.loc[row, 'SEDAMB Categories Outcome Reports'] = str(new_fields)

### program terms extract
print ('extracting program terms')

terms_list = program_df['Overlap'].tolist()

#convert terms to string
for i in range(len(terms_list)):
    terms_list[i] = str(terms_list[i])

#make spacy matcher out of terms list
matcher = PhraseMatcher(nlp.vocab)
patterns = [nlp(name) for name in terms_list]

matcher.add("Names", patterns)

#make new column
nsf_df['Program Terms'] = ['none']*len(nsf_df)

for row in range(0,len(nsf_df)):
    #empty the list
    programs_list=[]
    abstract = str(nsf_df.loc[row, 'Abstract']).lower()
    #if abstract:
    if not pd.isna(abstract):
        doc = nlp(abstract)
        for match_id, start, end in matcher(doc):
            #append to list
            programs_list.append(str(doc[start:end]))    
        #remove repeats
        programs_list=list(set(programs_list))
    else:
        programs_list=[]
    #add list to df
    prog_col = str(programs_list)
    prog_col = re.sub('\[','',prog_col)
    prog_col = re.sub('\]','',prog_col)

    nsf_df.loc[row, 'Program Terms'] = str(prog_col)

nsf_df['Program Terms'] = nsf_df['Program Terms'].str.replace('\'', '', regex=False)

## repeat for Outcome Reports
#make new column
nsf_df['Program Terms Outcome Reports'] = ['none']*len(nsf_df)

for row in range(0,len(nsf_df)):
    #empty the list
    programs_list=[]
    abstract = str(nsf_df.loc[row, 'Outcome Report']).lower()
    #if abstract:
    if not pd.isna(abstract):
        doc = nlp(abstract)
        for match_id, start, end in matcher(doc):
            #append to list
            programs_list.append(str(doc[start:end]))    
        #remove repeats
        programs_list=list(set(programs_list))
    else:
        programs_list=[]
    #add list to df
    prog_col = str(programs_list)
    prog_col = re.sub('\[','',prog_col)
    prog_col = re.sub('\]','',prog_col)

    nsf_df.loc[row, 'Program Terms Outcome Reports'] = str(prog_col)

nsf_df['Program Terms Outcome Reports'] = nsf_df['Program Terms Outcome Reports'].str.replace('\'nan\'', '', regex=False)
nsf_df['Program Terms Outcome Reports'] = nsf_df['Program Terms Outcome Reports'].str.replace('\[', '', regex=False)
nsf_df['Program Terms Outcome Reports'] = nsf_df['Program Terms Outcome Reports'].str.replace('\]', '', regex=False)
nsf_df['Program Terms Outcome Reports'] = nsf_df['Program Terms Outcome Reports'].str.replace('\'', '', regex=False)

### skills terms extract
print ('extracting skills')

terms_list = bg_df['data.name'].tolist()

#convert terms to string
for i in range(len(terms_list)):
    terms_list[i] = str(terms_list[i]).lower()

#make spacy matcher out of terms list
matcher = PhraseMatcher(nlp.vocab)
patterns = [nlp(name) for name in terms_list]

matcher.add("Names", patterns)

#make new column
nsf_df['Lightcast Skills'] = ['none']*len(nsf_df)

for row in range(0,len(nsf_df)):
    #empty the list
    programs_list=[]
    abstract = str(nsf_df.loc[row, 'Abstract']).lower()
    #if abstract:
    if not pd.isna(abstract):
    
        doc = nlp(abstract)
        for match_id, start, end in matcher(doc):
            #append to list
            programs_list.append(str(doc[start:end]))
            
        #remove repeats
        programs_list=list(set(programs_list))
    else:
        programs_list=[]
    #add list to df
    prog_col = str(programs_list)
    prog_col = re.sub('\[','',prog_col)
    prog_col = re.sub('\]','',prog_col)
    prog_col = re.sub('\'','',prog_col)
    
    nsf_df.loc[row, 'Lightcast Skills'] = str(prog_col)

## Repeat for outcome reports

#make new column
nsf_df['Lightcast Skills Outcome Reports'] = ['none']*len(nsf_df)

for row in range(0,len(nsf_df)):
    #empty the list
    programs_list=[]
    abstract = str(nsf_df.loc[row, 'Outcome Report']).lower()
    #if abstract:
    if not pd.isna(abstract):
    
        doc = nlp(abstract)
        for match_id, start, end in matcher(doc):
            #append to list
            programs_list.append(str(doc[start:end]))
            
        #remove repeats
        programs_list=list(set(programs_list))
    else:
        programs_list=[]
    #add list to df
    prog_col = str(programs_list)
    prog_col = re.sub('\[','',prog_col)
    prog_col = re.sub('\]','',prog_col)
    prog_col = re.sub('\'','',prog_col)

    nsf_df.loc[row, 'Lightcast Skills Outcome Reports'] = str(prog_col)

##clean up columns by subsetting to only columns we want to keep
# List of columns to keep
desired_columns = ['AwardNumber', 'Title', 'NSFOrganization', 'Program(s)', 'StartDate', 
                   'LastAmendmentDate', 'PrincipalInvestigator', 'State', 'Organization', 
                   'AwardInstrument', 'ProgramManager', 'EndDate', 'AwardedAmountToDate', 
                   'Co-PIName(s)', 'PIEmailAddress', 'OrganizationStreet', 'OrganizationCity', 
                   'OrganizationState', 'OrganizationZip', 'Full Address', 'OrganizationPhone', 
                   'NSFDirectorate', 'ProgramElementCode(s)', 'ProgramReferenceCode(s)', 'ARRAAmount', 
                   'Abstract', 'Outcome Report', 'Disciplines', 'Disciplines Outcome Reports', 
                   'DisciplineBroadArea', 'DisciplineBroadArea Outcome Reports', 'SEDAMB Categories',
                    'SEDAMB Categories Outcome Reports', 'Program Terms', 'Program Terms Outcome Reports', 
                    'Lightcast Skills', 'Lightcast Skills Outcome Reports']

# Filter the DataFrame to keep only the desired columns
nsf_df = nsf_df[desired_columns]

###save data with new columns
nsf_df.to_csv('../output/grants.csv', index=False)


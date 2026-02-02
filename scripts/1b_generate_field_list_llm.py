### alternate script to extract field/discipline terms to generate term list for broader extraction
# use O llama to generate lists of discipline terms
# takes grants_1.csv as input
# returns a new version of grants_1.csv with three new columns as well as discipline_terms_llm.csv

import ollama
import pandas as pd
import re

# import grant data
nsf_df = pd.read_csv("../output/grants_1.csv")

### prompt 1 (used in combination with manual list to generate final discipline list)
## loop df rows/extracted sentences and request discipline terms
nsf_df['extracted_disc_llm1_round1'] = ['none']*len(nsf_df)

for row in range(0, len(nsf_df)):
    print (row)
    #set abstract
    abstract = nsf_df.loc[row, 'Abstract']
    #query ollama
    response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': 'Format your response as a python list. Make a list of the discpilines, fields, or departments named in the following text:'+abstract}
    ])
    answer = str (response['message']['content'])
    #remove other parts of the response just leave the list
    match = re.search('\[([^\]]*)\]', answer)
    try:
        field_list = match.group(0)
    #exception for rows which the llm either formats incorrectly or finds no disciplines
    except:
        pass
    else:
        nsf_df.loc[row, 'extracted_disc_llm1'] = field_list

##run prompt 1 for a second round
nsf_df['extracted_disc_llm1_round2'] = ['none']*len(nsf_df)

for row in range(0, len(nsf_df)):
    print (row)
    #set abstract
    abstract = nsf_df.loc[row, 'Abstract']
    #query ollama
    response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': 'Format your response as a python list. Make a list of the discpilines, fields, or departments named in the following text:'+abstract}
    ])
    answer = str (response['message']['content'])
    #remove other parts of the response just leave the list
    match = re.search('\[([^\]]*)\]', answer)
    try:
        field_list = match.group(0)
    #exception for rows which the llm either formats incorrectly or finds no disciplines
    except:
        pass
    else:
        nsf_df.loc[row, 'extracted_disc_llm1'] = field_list

### run with prompt 2 for validation
## loop df rows/extracted sentences and pull out discipline terms
nsf_df['extracted_disc_llm2'] = ['none']*len(nsf_df)

for row in range(0, len(nsf_df)):
    print (row)
    #set abstract
    abstract = nsf_df.loc[row, 'Abstract']
    #query ollama
    response = ollama.chat(model='llama3', messages=[
        {'role': 'user', 'content': 'Format your response as a python list. Using only words from the text, make a list of the discpilines, fields, or departments named in the following text:'+abstract}
    ])
    answer = str (response['message']['content'])
    #remove everything but the list
    match = re.search('\[([^\]]*)\]', answer)
    try:
        field_list = match.group(0)
    except:
        print ("none")
    else:
        print (field_list)
        nsf_df.loc[row, 'extracted_disc_llm2'] = field_list

##generate list of terms for matching from prompt 1 results
#take all terms in single or double quotes
disc_all_string = nsf_df['extracted_disc_llm1'].str.cat(sep=' ')
disc_list = re.findall(r'(["\'])(.*?)\1', disc_all_string)

disc_list = [i[1] for i in disc_list]

#remove caps
disc_list = [i.lower() for i in disc_list]

#remove duplicates
disc_list = list(set(disc_list))
disc_list.sort()

#save discipline terms list
disc_df = pd.DataFrame(disc_list, columns=['terms'])
disc_df.to_csv("../output/discipline_terms_llm.csv")

#save grants csv
nsf_df.to_csv("../output/grants_1.csv", index=False)


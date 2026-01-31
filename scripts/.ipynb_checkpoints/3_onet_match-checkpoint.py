###script to match onet skills
##create an embedding space of O*NET skills and then of abstracts based on similarity of skills
#takes as input grants.csv and Content Model Reference.xlsx
#creates as output an updated grants.csv and the validation spreadsheet onet_matching.csv

#imports
import pandas as pd
import numpy as np
import re
from sentence_transformers import SentenceTransformer, util
model = SentenceTransformer('paraphrase-MiniLM-L6-v2')
from sklearn.manifold import TSNE
from nltk.tokenize import sent_tokenize, word_tokenize
import torch

##grant data
nsf_df = pd.read_csv('../output/grants.csv')

##O*NET skills database (from https://www.onetcenter.org/database.html#all-files)
onet_df = pd.read_excel('../input/Content Model Reference.xlsx')

#create broad category labels
##broadest label
onet_df['Category'] = onet_df['Element ID'].astype(str).str[0]
##second broadest label
onet_df['Category2'] = onet_df['Element ID'].astype(str).str[:3]


#limit skills to categories 1a 4a (following Sabet et al) 
# and 2 ("skills knowledge education")
# and tasks, technology skills
onet_df = onet_df[onet_df["Category2"].isin(['1.A', '4.A', '2.A', '2.B', '2.C', '2.D'])]
#remove header rows- rows where 'Element ID' has fewer than 4 characters
onet_df = onet_df[onet_df['Element ID'].str.len()>3]

#reset index
onet_df = onet_df.reset_index(drop=True)

#drop repeated 'Engineering and Technology'
onet_df = onet_df.drop(125)

#reset index
onet_df = onet_df.reset_index(drop=True)

##create embedding from O*NET description
#using pretrained sentence-transformers model
sentences = onet_df['Description']
embedding = model.encode(sentences)

##create dataframe of sentences and embeddings
d = {'element':onet_df['Element Name'], 'sent': sentences, 
     'embed': embedding.tolist(), 'label1':onet_df['Category'],
    'label2':onet_df['Category2']}
embeddings_df = pd.DataFrame(data=d)

##create a new column in the dataframe and add all skills for which 
##cosine similarity to a sentence in that abstract is above a certain value

#set the embedding list as the O*Net skills embeddings
emb2_list = embedding

#set lists to fill for validation df
awards_list = []
match_sent = []
match_skill = []
cos_sim_values = []

#set list to fill for grants df column
onet_column = []

#loop through the abstracts
for j in range(len(nsf_df)):
    #tokenize the sentences in the abstract
    abstract = nsf_df['Abstract'][j]
    if not pd.isna(abstract):
        phrases = sent_tokenize(abstract)
        #set the award number to record in validation df
        award = nsf_df['AwardNumber'][j]
        #create empty list for skills
        skill_list = []
        #for each sentence
        for phrase in phrases:
            #encode that sentence in the pretrained model
            emb1 = model.encode(phrase)
        
            #create empty matrix for cosine measures
            cos_sim = []
    
            #calculate all the cosine simliarites
            for emb2 in emb2_list:
                sim_measure = util.pytorch_cos_sim(emb1, emb2)[0][0].item()
                cos_sim.append(sim_measure)
                if sim_measure >.5:
                    row = np.where(emb2_list == emb2)[0][0]
                    #record the award for validation df
                    awards_list.append(award)
                    #record the sentence for validation df
                    match_sent.append(phrase)
                    # record the matched skill for validation df
                    match_skill.append(embeddings_df['element'][row])
                    # record the value for validation df
                    cos_sim_values.append(sim_measure)
                    #add matched skill to list for grants df
                    skill_list.append(str(embeddings_df['element'][row]))
    
        #remove repeats
        skill_list=list(set(skill_list))
        #remove punctuation
        skill_list = str(skill_list)
        skill_list = re.sub('\[','',skill_list)
        skill_list = re.sub('\]','',skill_list)
        skill_list = re.sub('\'','',skill_list)
    #if abstract blank
    else:
        skill_list = ""
    onet_column.append(skill_list)

nsf_df ['O*Net Skills']= onet_column

### make validation dataframe
d = {'Award':awards_list, 'Sentence': match_sent, 
     'Skill': match_skill, 'Similarity Value':cos_sim_values}
validation_df = pd.DataFrame(data=d)
validation_df.to_csv('../output/onet_matching.csv', index=False)

## Repeat extraction for Outcome Reports
#set the embedding list as the O*Net skills embeddings
emb2_list = embedding

#set lists to fill for validation df
awards_list = []
match_sent = []
match_skill = []
cos_sim_values = []

#set list to fill for grants df column
onet_column = []

#loop through the abstracts
for j in range(len(nsf_df)):
    #tokenize the sentences in the abstract
    abstract = nsf_df['Outcome Report'][j]
    if not pd.isna(abstract):
        phrases = sent_tokenize(abstract)
        #set the award number to record in validation df
        award = nsf_df['AwardNumber'][j]
        #create empty list for skills
        skill_list = []
        #for each sentence
        for phrase in phrases:
            #encode that sentence in the pretrained model
            emb1 = model.encode(phrase)
        
            #create empty matrix for cosine measures
            cos_sim = []
    
            #calculate all the cosine simliarites
            for emb2 in emb2_list:
                sim_measure = util.pytorch_cos_sim(emb1, emb2)[0][0].item()
                cos_sim.append(sim_measure)
                if sim_measure >.5:
                    row = np.where(emb2_list == emb2)[0][0]
                    #record the award for validation df
                    awards_list.append(award)
                    #record the sentence for validation df
                    match_sent.append(phrase)
                    # record the matched skill for validation df
                    match_skill.append(embeddings_df['element'][row])
                    # record the value for validation df
                    cos_sim_values.append(sim_measure)
                    #add matched skill to list for grants df
                    skill_list.append(str(embeddings_df['element'][row]))
    
        #remove repeats
        skill_list=list(set(skill_list))
        #remove punctuation
        skill_list = str(skill_list)
        skill_list = re.sub('\[','',skill_list)
        skill_list = re.sub('\]','',skill_list)
        skill_list = re.sub('\'','',skill_list)
    #if abstract blank
    else:
        skill_list = ""
    onet_column.append(skill_list)

nsf_df ['O*Net Skills Outcome Reports']= onet_column

##save grants csv
nsf_df.to_csv('../output/grants.csv', index=False)




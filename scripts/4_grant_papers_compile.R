### script for combining and cleaning nsf and nih grant data
# requires three downloaded tables from sciscinet data lake: NSF_Link, Papers, and PaperDetails.
# also takes grants.csv as input, and outputs the table grant_papers.csv

#packages and libraries
install.packages("readr")
install.packages("data.table")
install.packages("here")

library(readr)
library(data.table)
library(here)
library(dplyr)

###make awards dataset
##bring in data
nsf_all <- fread('../output/grants.csv')
##delete extra columns
nsf_all <- nsf_all[, c("AwardNumber", "Abstract", "Outcome Report")]

###make papers dataset
##bring in sciscinet csvs- download from https://doi.org/10.6084/m9.figshare.c.6076908.v1
nsf_link_location <- '[INSERT SAVED LOCATION]'
papers_location <- '[INSERT SAVED LOCATION]'
paperdetails_location <- '[INSERT SAVED LOCATION]'

#start with the nsf crossover
ssn_nsf <- fread(nsf_link_location)

#match nsf award number field format
nsf_all$NSF_Award_Number<- paste0('NSF-',nsf_all$AwardNumber)

nsf_and_ssn <- merge(ssn_nsf, nsf_all, by="NSF_Award_Number")

#clean up
rm(nsf_all, ssn_nsf)

##create new matching dataframe that's just paper IDs
nsf_match <- nsf_and_ssn[, c("PaperID")]

### tackle papers by splitting data into 14 sections of 10 million to run on 16G memory
#create subset
ssn_papers1 <- fread(papers_location, nrows = 10000000)

# add paper data to dataframe using merge
nsf_match <- merge(nsf_match, ssn_papers1, by="PaperID", all.x = TRUE)

#clean up unneeded large dataframe
rm(ssn_papers1)

#set column names to reset bigger df when skipping rows in fread
headnames <- colnames(nsf_match)

##repeat for 12 more sections this time using rows_update to update existing columns
for (i in 1:12) {
  print (i)
  ssn_papers1 <- fread(papers_location, skip = (i*10000000), nrows = 10000000)
  colnames(ssn_papers1) <- headnames
  # Replaces NA values in df1 with matching IDs from df2
  nsf_match <- nsf_match %>% rows_update(ssn_papers1, by = "PaperID", unmatched = "ignore")
  rm(ssn_papers1)
  print (nrow(nsf_match[!is.na(nsf_match$DOI), ]))
}

#last section
ssn_papers1 <- fread(papers_location, skip = 130000000)
colnames(ssn_papers1) <- headnames
nsf_match <- nsf_match %>% rows_update(ssn_papers1, by = "PaperID", unmatched = "ignore")
rm(ssn_papers1)

###repeat previous section to add Paper Details columns, but with smaller chunks
ssn_papers1 <- fread(paperdetails_location, nrows = 5000000)

#create a new match df
nsf_match2 <- nsf_and_ssn[, c("PaperID")]

nsf_match2 <- merge(nsf_match2, ssn_papers1, by="PaperID", all.x = TRUE)

rm(ssn_papers1)

headnames <- colnames(nsf_match2)

for (i in 1:25) {
  print (i)
  ssn_papers1 <- fread(paperdetails_location, skip = (i*5000000), nrows = 5000000)
  colnames(ssn_papers1) <- headnames
  # Replaces NA values in df1 with matching IDs from df2
  nsf_match2 <- nsf_match2 %>% rows_update(ssn_papers1, by = "PaperID", unmatched = "ignore")
  rm(ssn_papers1)
  print (nrow(nsf_match2[!is.na(nsf_match2$DOI), ]))
}

#last section
ssn_papers1 <- fread(paperdetails_location, skip = 130000000)
colnames(ssn_papers1) <- headnames
nsf_match2 <- nsf_match2 %>% rows_update(ssn_papers1, by = "PaperID", unmatched = "ignore")
rm(ssn_papers1)

#merge the dataframes all together
nsf_and_ssn <- merge(nsf_and_ssn, nsf_match, by="PaperID")
nsf_and_ssn <- merge(nsf_and_ssn, nsf_match2, by="PaperID")

##get rid of merge artifacts
nsf_and_ssn <- unique(nsf_and_ssn)

##remove repeat columns
nsf_and_ssn <- subset(nsf_and_ssn, select = -c(DOI.y, DocType.y,Year.y,Date.y,JournalID.y,ConferenceSeriesID.y))
##rename repeat columns
nsf_and_ssn <- nsf_and_ssn %>% rename(DOI = DOI.x, DocType = DocType.x, Year = Year.x, Date = Date.x, JournalID = JournalID.x, ConferenceSeriesID = ConferenceSeriesID.x)

##save csv of papers with metadata
write.csv(nsf_and_ssn, file="../output/grant_papers.csv")

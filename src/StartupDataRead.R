

library(jsonlite)
library(dplyr)
library(tidyr)
library(purrr)


json_data <- fromJSON(r"(C:\Users\admin\OneDrive\Documents\GitHub\ExperimentEH\src\startup_data.json)", simplifyVector = FALSE)
#names(json_data)
startup_df <- do.call(rbind, lapply(json_data, function(entry) {
  # For each startup, attach the parent code and used fields
  do.call(rbind, lapply(entry$startups, function(s) {
    data.frame(code = entry$code,
               used = entry$used,
               Startup_name = s$Startup_name,
               Industry = s$Industry,
               Product_info = s$Product_info,
               Founded = s$Founded,
               Founder_age = s$Founder_age,
               Founder_Nstartups = s$Founder_Nstartups,
               Assigned_Founder = s$Assigned_Founder,
               Founder_gender = s$Founder_gender,
               Evaluation_sentence = s$Evaluation_sentence,
               Order = s$Order,
               stringsAsFactors = FALSE)
  }))
}))
names(startup_df)
#colnames(startup_df)[1] = "startup_code"
sum(startup_df$used==FALSE)
unique(startup_df$Order)
unique(startup_df$Startup_name)
unique(startup_df$Industry)
unique(startup_df$Founder_age)



#founder name
#founder gender
startup_df = startup_df %>%
  separate(Assigned_Founder, into = c("founder_firstname", "founder_lastname"), sep = " ")
unique(startup_df$founder_firstname)
unique(startup_df$founder_lastname)



#evaluator info
startup_df$Evaluation_sentence1 = startup_df$Evaluation_sentence
startup_df = startup_df %>%
  separate(Evaluation_sentence1, into = c("evaluator", "valuation"), sep = "\\$", extra = "merge") 
unique(startup_df$evaluator)



# gender composition in set
startup_df = startup_df %>% dplyr::group_by(code) %>% dplyr::mutate(
  nFemInSet = sum(Founder_gender=="female"),
  Fem_Order = which(Founder_gender=="female")
)
summary(startup_df$nFemInSet)
summary(startup_df$Fem_Order)
table(startup_df$Fem_Order)

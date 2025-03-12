# Library
library(shiny)
library(tidyverse)
library(DT)
library(shinythemes)
library(shinydashboard)
library(corrplot)
library(usmap)
library(shinyWidgets)
library(ggplot2)
library(FactoMineR)
library(Factoshiny)
library(readxl)
library(skimr)

# Chargement et préparation des données -----
df <- read_csv2("data/gpu_specs_v7.csv")
df2= read.csv2("data/CG_laptop.csv",sep=",")
# Transformation en facteurs des variables concernées -----
fact <- c(12:16)
df[fact] <- lapply(df[, fact], as.factor)

# Création de liste des données -----
quant_vars <- names(df)[sapply(df, is.numeric)]
#type_CG <- unique(df$type_CG)
marque <- unique(df$manufacturer)
IGP <- unique(df$igp)

# actives = df[,c(1,4,5,6,8,9,10,11)]
# centrage réduction
# data_scaled <- as.data.frame(scale(actives[, -1]))
# data_scaled$ETAT <- actives$ETAT
# quant_vars_actives = names(actives)[sapply(actives, is.numeric)]

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
df <- read.csv2("data/CG_PC.csv",sep=",")
df2= read.csv2("data/CG_laptop.csv",sep=",")
# Transformation en facteurs des variables concernées -----
fact <- c(1:3,11:14)
df[fact] <- lapply(df[, fact], as.factor)
df$memSize = as.numeric(df$memSize)
# Création de liste des données -----
quant_vars <- names(df)[sapply(df, is.numeric)]
#type_CG <- unique(df$type_CG)
marque <- unique(df$manufacturer)
IGP <- unique(df$igp)

qual_vars <- names(df)[sapply(df, is.factor)]   # Variables qualitatives (facteurs ou catégoriques)

# actives = df[,c(1,4,5,6,8,9,10,11)]
# centrage réduction
# data_scaled <- as.data.frame(scale(actives[, -1]))
# data_scaled$ETAT <- actives$ETAT
# quant_vars_actives = names(actives)[sapply(actives, is.numeric)]

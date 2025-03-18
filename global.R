# Chargement des bibliothèques nécessaires -----
library(shiny)
library(gganimate)
library(tidyverse)
library(DT)
library(shinythemes)
library(shinydashboard)
library(FactoMineR)
library(factoextra)
library(ggplot2)
library(corrplot)
library(skimr)
library(shinyjs)
library(plotly)
library(caret)  # For machine learning algorithms
library(randomForest)
library(e1071)
library(class)  # For KNN
library(cluster)  # For k-means

# Function to train a Random Forest model
train_random_forest <- function(data, target) {
  model <- randomForest(as.formula(paste(target, "~ .")), data = data)
  return(model)
}

# Function to train an SVM model
train_svm <- function(data, target) {
  model <- svm(as.formula(paste(target, "~ .")), data = data)
  return(model)
}

# Function to evaluate the model
evaluate_model <- function(model, data, target) {
  predictions <- predict(model, data)
  confusionMatrix(predictions, data[[target]])
}


# Function to train a KNN model
train_knn <- function(data, target, k) {
  train_data <- data[-which(names(data) == target)]
  train_target <- data[[target]]
  knn_model <- knn(train = train_data, test = train_data, cl = train_target, k = k)
  return(knn_model)
}

# Function to perform k-means clustering
perform_kmeans <- function(data, centers) {
  kmeans_model <- kmeans(data, centers)
  return(kmeans_model)
}

# Function to evaluate the KNN model
evaluate_knn <- function(model, data, target) {
  predictions <- model
  confusionMatrix(predictions, data[[target]])
}

# Chargement des données -----
# Assurez-vous que les chemins sont corrects et adaptés à vos fichiers
df <- read.csv2("data/CG_PC.csv",sep=",",dec=".")
#Identifier les doublons selon les trois premières colonnes
duplicated_rows <- df[duplicated(df[, 1:3]) | duplicated(df[, 1:3], fromLast = TRUE), ]
df<- df[!duplicated(df[, 1:3]), ]
# Préparation et nettoyage des données -----
# Transformation des colonnes en facteurs (si applicable)
fact <- c(1:2,11:14)  # Indices des colonnes à transformer en facteurs (ajustez selon vos données)
df[fact] <- lapply(df[, fact], as.factor)

# Création des listes pour les variables quantitatives et qualitatives -----
# Variables quantitatives (numériques)
quant_vars <- names(df)[sapply(df, is.numeric)]

# Variables qualitatives (facteurs ou catégoriques)
qual_vars <- names(df)[sapply(df, is.factor)]

# Variables actives pour l'ACP (quantitatives uniquement)
quant_vars_actives <- quant_vars  # Modifiez ici si vous voulez limiter les variables spécifiques à l'ACP.

# Variables catégorielles pour l'ACP
cat_vars <- qual_vars  # Utilisé pour ajouter des catégories dans certaines visualisations de l'ACP.

# Préparation pour les filtres dans la barre latérale -----
# Extraction des valeurs uniques pour les champs nécessaires
IGP <- unique(df$

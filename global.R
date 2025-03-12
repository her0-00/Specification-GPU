# Chargement des bibliothèques nécessaires -----
library(shiny)
library(tidyverse)
library(DT)
library(shinythemes)
library(shinydashboard)
library(FactoMineR)
library(factoextra)
library(ggplot2)
library(skimr)
library(shinyjs)
# Chargement des données -----
# Assurez-vous que les chemins sont corrects et adaptés à vos fichiers
df <- read_csv2("data/gpu_specs_v7.csv")
df2 <- read.csv2("data/CG_laptop.csv", sep = ",")

# Préparation et nettoyage des données -----
# Transformation des colonnes en facteurs (si applicable)
fact <- c(12:16)  # Indices des colonnes à transformer en facteurs (ajustez selon vos données)
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
IGP <- unique(df$igp)  # Assurez-vous que "igp" est une colonne existante
marque <- unique(df$manufacturer)  # Assurez-vous que "manufacturer" est une colonne existante

# Gestion des valeurs manquantes -----
# Si vous voulez supprimer ou manipuler les valeurs manquantes, vous pouvez utiliser :
# df <- na.omit(df)  # Supprime les lignes avec des valeurs manquantes
# Ou bien, remplissez les valeurs manquantes avec une valeur par défaut :
# df[is.na(df)] <- 0

# Notes :
# 1. Assurez-vous que les colonnes mentionnées dans `fact`, `igp` et `manufacturer` existent dans vos données.
# 2. Vérifiez les données pour éviter les erreurs dues à des types de données incorrects (e.g., colonnes numériques mal importées).
# 3. Modifiez `quant_vars_actives` et `cat_vars` si vous voulez restreindre les variables disponibles pour certaines analyses.

# Options supplémentaires pour visualisation -----
# (Optionnel) Vous pouvez ajouter des palettes de couleurs ou des paramètres globaux pour ggplot2, par exemple :
theme_set(theme_minimal())  # Définit un thème global pour les graphiques

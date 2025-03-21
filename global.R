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

# Chargement des données -----
# Assurez-vous que les chemins sont corrects et adaptés à vos fichiers
df <- read.csv2("data/CG_ALL.csv", sep = ",", dec = ".")

# Préparation et nettoyage des données -----
# Transformation des colonnes en facteurs (si applicable)
fact <- c(1:2, 11:14)  # Indices des colonnes à transformer en facteurs (ajustez selon vos données)
df[fact] <- lapply(df[, fact], as.factor)
min_year <- min(df$releaseYear)
max_year <- max(df$releaseYear)

# Variables quantitatives (numériques)
quant_vars <- names(df)[sapply(df, is.numeric)][2:8]

# Variables qualitatives (facteurs ou catégoriques)
qual_vars <- names(df)[sapply(df, is.factor)]

# Variables actives pour l'ACP (quantitatives uniquement)
quant_vars_actives <- quant_vars  # Modifiez ici si vous voulez limiter les variables spécifiques à l'ACP.

# Variables catégorielles pour l'ACP
cat_vars <- qual_vars 

# Préparation pour les filtres dans la barre latérale -----
# Extraction des valeurs uniques pour les champs nécessaires
IGP <- unique(df$igp)  # Assurez-vous que "igp" est une colonne existante
marque <- unique(df$manufacturer)  # Assurez-vous que "manufacturer" est une colonne existante
marq_ <- unique(df$manufacturer)  # Définition de marq_
theme_set(theme_minimal())  # Définit un thème global pour les graphiques







# Fonction pour calculer la matrice de variances-covariances
get_S <- function(data) {
  if (!is.data.frame(data)) {
    stop("Les données doivent être sous forme de data.frame")
  }
  
  # Vérifier qu'il y a des colonnes numériques pour le calcul
  numeric_data <- data[sapply(data, is.numeric)]
  if (ncol(numeric_data) == 0) {
    stop("Aucune variable quantitative valide trouvée pour calculer la matrice des variances-covariances")
  }
  
  # Calculer la matrice de variances-covariances
  return(cov(numeric_data, use = "complete.obs"))
}

# Fonction pour calculer les valeurs propres et les vecteurs propres
get_LambdasAndEigenVectors <- function(data) {
  if (!is.data.frame(data)) {
    stop("Les données doivent être sous forme de data.frame")
  }
  
  # Vérifier qu'il y a des colonnes numériques
  numeric_data <- data[sapply(data, is.numeric)]
  if (ncol(numeric_data) == 0) {
    stop("Aucune variable quantitative valide trouvée pour calculer les valeurs propres")
  }
  
  # Calcul de la décomposition en valeurs propres
  eigen_res <- eigen(cov(numeric_data, use = "complete.obs"))
  return(list(lambdas = eigen_res$values, vectors = eigen_res$vectors))
}

# Fonction pour calculer le pourcentage d'inertie totale
get_InertiaAxes <- function(data) {
  eigen_res <- get_LambdasAndEigenVectors(data)
  inertia_percentages <- (eigen_res$lambdas / sum(eigen_res$lambdas)) * 100
  return(inertia_percentages)
}

# Fonction pour réaliser l'ACP
doitPerformACP <- function(data, vars) {
  df_selected <- data[, vars, drop = FALSE]
  df_selected <- scale(df_selected)  # Centrage et réduction
  row.names(df_selected) <- row.names(data)
  acp_result <- PCA(df_selected, scale.unit = TRUE, graph = FALSE)
  return(acp_result)
}

reactive_acp <- reactiveValues(result = NULL, selected_vars = NULL)

# Mise à jour des variables de l'ACP
update_acp <- function(input, df) {
  if (!is.null(input$acp_vars) && length(input$acp_vars) > 1) {
    reactive_acp$selected_vars <- input$acp_vars
    reactive_acp$result <- doitPerformACP(df, input$acp_vars)
  } else {
    reactive_acp$result <- NULL
    reactive_acp$selected_vars <- NULL
  }
}
plot_acp_ind <- function(acp_result, df, color_var, contrib_value) {
  # Coloration par cos2 si aucune variable catégorielle n'est sélectionnée
  fviz_pca_ind(acp_result,
               repel = TRUE,
               pointsize = 1,  # Réduire la taille des points
               col.ind = "cos2",  # Rétablir la coloration basée sur la colonne manufacturer
               gradient.cols = c("#00AFBB", "black", "red"), 
               alpha.ind = 0.5,  # Transparence des points
               select.ind = list(cos2 = contrib_value))  # Sélectionner les individus avec les plus grandes contributions
}

plot_acp_var <- function(acp_result, selected_vars) {
  fviz_pca_var(acp_result, 
               repel = TRUE, 
               col.var = "contrib", 
               gradient.cols = c("#00AFBB", "black", "red"),
               select.var = list(name = selected_vars))  # Sélectionner uniquement les variables actives choisies
}

plot_acp_biplot <- function(acp_result, df, color_var, selected_vars, contrib_value) {
  if (!is.null(color_var) && color_var %in% names(df) && color_var != "") {
    fviz_pca_biplot(acp_result, 
                    repel = TRUE, 
                    label = "all", 
                    habillage = df[[color_var]],  # Coloration par variable catégorielle
                    select.var = list(name = selected_vars),  # Sélectionner les variables choisies
                    addEllipses = TRUE, 
                    arrows = TRUE,  # Affiche bien les vecteurs des variables
                    palette = "jco",
                    select.ind = list(cos2 = contrib_value))
  } else {
    fviz_pca_biplot(acp_result, 
                    repel = TRUE, 
                    label = "all", 
                    col.ind = "cos2",  # Coloration des individus selon cos2
                    gradient.cols = c("#00AFBB", "black", "red"),
                    select.var = list(name = selected_vars), 
                    select.ind = list(cos2 = contrib_value),
                    arrows = TRUE)  # Forcer l'affichage des vecteurs
  }
}


# Filtrage des données
filtered_acp_data_ <- df %>%
  filter( igp == "No",manufacturer==marq_,releaseYear >= 2022, releaseYear <= 2025)




c <- doitPerformACP(filtered_acp_data_, quant_vars)
print("ACP Result:")
print(c)  # Affiche le résultat de l'ACP

# Extraire les valeurs cos2
cos2_values <- c$ind$cos2
print("Cos2 Values:")
print(cos2_values)  # Affiche les valeurs cos2

# Sélectionner les meilleurs individus basés sur la somme des cos2
total_cos2 <- rowSums(cos2_values[, 1:2])
top_individuals <- order(total_cos2, decreasing = TRUE)[1:50]
print("Top Individuals:")
print(top_individuals)  # Affiche les meilleurs individus

# Filtrer les données des meilleurs individus
filtered_acp_data_ <- filtered_acp_data_[top_individuals, , drop = FALSE]
print("Filtered ACP Data:")
print(filtered_acp_data_)  # Affiche les données filtrées pour l'ACP

# Sélectionner les colonnes selon les variables de l'ACP
selected_columns <- quant_vars
print("Selected Columns:")
print(selected_columns)  # Affiche les colonnes sélectionnées

# Appliquer la mise à l'échelle des données pour l'ACP
df_ACP_1 <- filtered_acp_data_[, selected_columns, drop = FALSE] %>%scale(center = TRUE, scale = TRUE)
print("Scaled ACP Data (df_ACP_1):")
print(df_ACP_1)  # Affiche les données mises à l'échelle pour l'ACP

# Nombre de points distincts dans les données
distinct_points <- nrow(unique(df_ACP_1))
print("Number of Distinct Points:")
print(distinct_points)  # Affiche le nombre de points distincts


# Effectuer le clustering avec le nombre optimal de clusters
cl2 <- kmeans(x = df_ACP_1, centers = 5, nstart = 100)
print("Clustering Result (cl2):")
print(cl2)  # Affiche les résultats du clustering

# Ajouter les clusters aux données filtrées
filtered_acp_data_$Cluster <- cl2$cluster

# Affichage des moyennes techniques 
cluster_summary <- filtered_acp_data_ %>%
  group_by(Cluster) %>%
  summarise(
    `Moyenne VRAM (Go)` = round(mean(memSize, na.rm = TRUE), 1),
    `Moyenne GPU Clock (MHz)` = round(mean(gpuClock, na.rm = TRUE), 0),
    `Moyenne memBusWidth (bits)` = round(mean(memBusWidth, na.rm = TRUE), 0),
    `Moyenne unifiedShader` = round(mean(unifiedShader, na.rm = TRUE), 0),
    `Moyenne memClock (MHz)` = round(mean(memClock, na.rm = TRUE), 0),
    `Moyenne année de sortie` = round(mean(releaseYear, na.rm = TRUE), 0),
    `Cartes dans ce cluster` = n()
  )

dev_ia_cluster <- cluster_summary %>% filter(`Moyenne unifiedShader` == max(`Moyenne unifiedShader`)) %>% pull(Cluster)
console_jeux_cluster <- cluster_summary %>% filter(`Moyenne memBusWidth (bits)` == min(`Moyenne memBusWidth (bits)`)) %>% pull(Cluster)
usage_general_cluster <- cluster_summary %>% filter(`Moyenne GPU Clock (MHz)` == max(`Moyenne GPU Clock (MHz)`)) %>% pull(Cluster)
data_center_cluster <- cluster_summary %>% filter(`Moyenne VRAM (Go)` == max(`Moyenne VRAM (Go)`)) %>% pull(Cluster)

cluster_summary <- cluster_summary %>%
  mutate(`Profil_recommande` = case_when(
    Cluster == dev_ia_cluster ~ "Dev IA Grand Public",
    Cluster == console_jeux_cluster ~ "Console de jeux",
    Cluster == usage_general_cluster ~ "Performances Modérées pour Usage Général",
    Cluster == data_center_cluster ~ "Calcul Intensif et Data Center",
    TRUE ~ "Haut de Gamme pour Professionnels et Gaming"
  ))
filtered_acp_data_=  filtered_acp_data_%>%
  mutate(`Profil_recommande` = case_when(
    Cluster == dev_ia_cluster ~ "Dev IA Grand Public",
    Cluster == console_jeux_cluster ~ "Console de jeux",
    Cluster == usage_general_cluster ~ "Performances Modérées pour Usage Général",
    Cluster == data_center_cluster ~ "Calcul Intensif et Data Center",
    TRUE ~ "Haut de Gamme pour Professionnels et Gaming"
  ))
filtered_acp_data_summarise<- cluster_summary


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
df <- read.csv2("data/CG_ALL.csv",sep=",",dec=".")
#Identifier les doublons selon les trois premières colonnes
duplicated_rows <- df[duplicated(df[, 1:3]) | duplicated(df[, 1:3], fromLast = TRUE), ]
df<- df[!duplicated(df[, 1:3]), ]
# Préparation et nettoyage des données -----
# Transformation des colonnes en facteurs (si applicable)
fact <- c(1:2,11:14)  # Indices des colonnes à transformer en facteurs (ajustez selon vos données)
df[fact] <- lapply(df[, fact], as.factor)


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
actives <- df[, c(3:10)]
# Normalisation des variables quantitatives
data_scaled <- as.data.frame(scale(actives[, -1]))
quant_vars_actives <- colnames(actives[, -1])
update_acp <- function(input, df) {
  if (!is.null(input$acp_vars) && length(input$acp_vars) > 1) {
    reactive_acp$selected_vars <- input$acp_vars
    reactive_acp$result <- doitPerformACP(df, input$acp_vars)
  } else {
    reactive_acp$result <- NULL
    reactive_acp$selected_vars <- NULL
  }
}

doitPerformACP <- function(data, vars) {
  df_selected <- data[, vars, drop = FALSE]
  df_selected <- scale(df_selected)  # Centrage et réduction
  row.names(df_selected) <- row.names(data)
  acp_result <- PCA(df_selected, scale.unit = TRUE, graph = FALSE)
  return(acp_result)
}
reactive_acp <- reactiveValues(result = NULL, selected_vars = NULL)

plot_acp_ind <- function(acp_result, df,color_var, contrib_value) {
  if (!is.null(color_var) && color_var %in% names(df) && color_var != "") {
    # Coloration par variable catégorielle si sélectionnée
    fviz_pca_ind(acp_result,
                 repel = TRUE,
                 pointsize = 1,  # Réduire la taille des points
                 habillage = df[[color_var]],  # Utilisation de la variable catégorielle
                 addEllipses = TRUE,  # Ajout des ellipses de concentration
                 palette = "jco", 
               alpha.ind = 0.5,  # Transparence des points
                 select.ind = list(cos2 = contrib_value))  # Sélectionner les individus avec les plus grandes contributions
  } else {
    # Coloration par cos2 si aucune variable catégorielle n'est sélectionnée
    fviz_pca_ind(acp_result,
                 repel = TRUE,
                 pointsize = 1,  # Réduire la taille des points
                 col.ind = "cos2",  # Rétablir la coloration basée sur la colonne manufacturer
                 gradient.cols = c("#00AFBB", "black", "red"), 
                 alpha.ind = 0.5,  # Transparence des points
                 select.ind = list(cos2 = contrib_value))  # Sélectionner les individus avec les plus grandes contributions
  }
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

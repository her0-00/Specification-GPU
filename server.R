server <- function(input, output, session) {
  
  # Sélectionner toutes les options dans les filtres
  observeEvent(input$select_all, {
    updateSelectInput(session, "IGP", selected = IGP)
    updateSelectInput(session, "Marque", selected = marque)
  })
  
  # Filtrer les données selon les choix de l'utilisateur
  filtered_data <- reactive({
    req(input$IGP, input$Marque)
    
    df_filtered <- df %>%
      filter(igp %in% input$IGP, manufacturer %in% input$Marque)
    
    if (input$IGP == "Yes") {
      df_filtered <- df_filtered[, !(names(df_filtered) %in% c("memClock", "memType"))]
    }
    
    df_filtered
    
  })
  
  # Création des listes pour les variables quantitatives et qualitatives en utilisant les données filtrées
  observe({
    df_data <- filtered_data()
    
    # Variables quantitatives (numériques)
    quant_vars <- names(df_data)[sapply(df_data, is.numeric)]
    
    # Variables qualitatives (facteurs ou catégoriques)
    qual_vars <- names(df_data)[sapply(df_data, is.factor)]
    
    # Variables actives pour l'ACP (quantitatives uniquement)
    quant_vars_actives <- quant_vars  # Modifiez ici si vous voulez limiter les variables spécifiques à l'ACP.
    
    # Variables catégorielles pour l'ACP
    cat_vars <- qual_vars 
    
    updateSelectInput(session, "var_quanti", choices = quant_vars)
    updateSelectInput(session, "var_quali", choices = qual_vars)
    updateSelectInput(session, "acp_vars", choices = quant_vars)
    updateSelectInput(session, "acp_cat_vars", choices = qual_vars)
  })
  
  # Filtrer les données selon la marque et la plage d'années sélectionnées
  filtered_acp_data <- reactive({
    req(input$selected_brand, input$year_range)
    filtered_data() %>%
      filter(manufacturer == input$selected_brand, releaseYear >= input$year_ranges[1], releaseYear <= input$year_ranges[2])
  })
  
  # Générer la table des données
  output$table <- renderDataTable({
    datatable(filtered_data(), options = list(
      pageLength = 10,
      scrollX = TRUE,
      dom = 'Bfrtip',
      buttons = c('copy', 'csv', 'excel')
    ))
  })
  
  # Générer les statistiques descriptives
  output$desc_stats <- renderDataTable({
    req(filtered_data())
    skim(filtered_data()) %>%
      dplyr::select(skim_type, skim_variable, n_missing, complete_rate, numeric.mean, numeric.sd, numeric.p0, numeric.p50) %>%
      datatable(options = list(scrollX = TRUE, pageLength = 5))
  })
  
  # Télécharger les données filtrées
  output$downloadData <- downloadHandler(
    filename = function() { paste("filtered_data_", Sys.Date(), ".csv", sep = "") },
    content = function(file) {
      write.csv(filtered_data(), file)
    }
  )
  
  output$downloadData2 <- downloadHandler(
    filename = function() { paste("desc_stats_", Sys.Date(), ".csv", sep = "") },
    content = function(file) {
      desc_stats <- skim(filtered_data()) %>%
        dplyr::select(skim_type, skim_variable, n_missing, complete_rate, numeric.mean, numeric.sd, numeric.p0, numeric.p50)
      write.csv(desc_stats, file)
    }
  )
  
  # HISTOGRAMME
  output$histogram <- renderPlotly({
    req(input$var_quanti)  
    p <- ggplot(filtered_data(), aes_string(x = input$var_quanti)) +
      geom_histogram(binwidth = 10, fill = "blue", color = "black", alpha = 0.7) +
      labs(
        title = paste("Histogramme de", input$var_quanti),
        x = input$var_quanti,
        y = "Fréquence"
      ) 
    ggplotly(p)  # Conversion en graphique interactif
  })
  
  # Boxplot
  output$boxplot <- renderPlotly({
    req(input$var_quanti)  # Vérification qu'une variable quantitative est choisie
    
    # Création du boxplot
    p <- ggplot(filtered_data(), aes_string(y = input$var_quanti)) +
      geom_boxplot(fill = "orange", color = "black", alpha = 0.7) +
      labs(
        title = paste("Boxplot de", input$var_quanti),
        y = input$var_quanti
      ) +
      theme_minimal()
    
    ggplotly(p)  # Conversion en graphique interactif
  })
  
  # Visualisation des répartitions qualitatives
  output$qualitative_table <- renderDataTable({
    req(input$var_quali)
    filtered_data() %>%
      group_by(.data[[input$var_quali]]) %>%
      summarise(Count = n()) %>%
      datatable(options = list(pageLength = 5))
  })
  
  # Implémentation de l'ACP
  
  # Sélectionne ou désélectionne toutes les variables pour l'ACP -----
  observeEvent(input$select_all, {
    current_selection <- input$acp_vars 
    if (length(current_selection) < length(quantitative_vars)) {
      updateSelectInput(session, "acp_vars", selected = quantitative_vars)
    } else {
      updateSelectInput(session, "acp_vars", selected = character(0))
    }
  })
  # Execution de l'ACP ----
  observeEvent(input$run_acp, {
    if (!is.null(input$acp_vars) && length(input$acp_vars) > 1) {
      reactive_acp$selected_vars <- input$acp_vars
      print("Selected Variables for ACP:")
      print(reactive_acp$selected_vars)  # Print selected variables for ACP
      
      reactive_acp$result <- doitPerformACP(filtered_acp_data(), input$acp_vars)
      print("ACP Result:")
      print(reactive_acp$result)  # Print ACP result
      
      # Filter individuals based on cos2 values
      cos2_values <- reactive_acp$result$ind$cos2
      print("Cos2 Values:")
      print(cos2_values)  # Print cos2 values
      
      # Select the top input$contrib_value individuals based on their cos2 values
      total_cos2 <- rowSums(cos2_values[,1:2])
      top_individuals <- order(total_cos2, decreasing = TRUE)[1:input$contrib_value]
      print("Top Individuals:")
      print(top_individuals)  # Print top individuals
      
      filtered_acp_data <- filtered_acp_data()[top_individuals, , drop = FALSE]
      print("Filtered ACP Data:")
      print(filtered_acp_data)  # Print filtered ACP data
      
      # Ensure that df_ACP_1 has the same columns as the data used for the ACP
      selected_columns <- reactive_acp$selected_vars
      print("Selected Columns:")
      print(selected_columns)  # Print selected columns
      
      df_ACP_1 <- filtered_acp_data[, selected_columns, drop = FALSE] %>% scale(center = TRUE, scale = TRUE)
      print("Scaled ACP Data (df_ACP_1):")
      print(df_ACP_1)  # Print scaled ACP data
      
      # Determine the optimal number of clusters using the "within-cluster sum of squares" method
      output$nb_clust <- renderPlot({
        fviz_nbclust(df_ACP_1, kmeans, method = "wss", k.max = 10, nstart = 100) +
          labs(title = "Elbow Method for Optimal Number of Clusters")
      })
      
      # Check the number of distinct points in the dataset
      distinct_points <- nrow(unique(df_ACP_1))
      print("Number of Distinct Points:")
      print(distinct_points)  # Print number of distinct points
      
      # Ensure the number of clusters does not exceed the number of distinct points
      num_clusters <- input$n_cluster
      print("Number of Clusters:")
      print(num_clusters)  # Print number of clusters
      
      # Perform clustering with the optimal number of clusters
      cl2 <- kmeans(x = df_ACP_1, centers = num_clusters, nstart = 100)
      print("Clustering Result (cl2):")
      print(cl2)  # Print clustering result
      
      # Plot the clusters
      output$cluster_plot <- renderPlot({
        fviz_cluster(cl2, geom = "point", data = df_ACP_1, label = rownames(filtered_acp_data)) +
          labs(title = "Clustering des individus en ACP",
               x = "PC1",
               y = "PC2")
      })
    } else {
      reactive_acp$result <- NULL
      reactive_acp$selected_vars <- NULL
    }
  })
  
  # Affichage des résultats de l'ACP
  output$acp_ind_plot <- renderPlot({
    req(reactive_acp$result)
    plot_acp_ind(reactive_acp$result, filtered_data(), input$acp_cat_vars, input$contrib_value)
  })
  
  # Tracer les graphiques des variables
  output$acp_var_plot <- renderPlot({
    req(reactive_acp$result)
    plot_acp_var(reactive_acp$result, input$acp_vars)
  })
  
  observeEvent(input$apply_cat, {
    update_acp(input, filtered_data())
  })
  
  output$biplot <- renderPlot({
    req(reactive_acp$result)
    plot_acp_biplot(reactive_acp$result, filtered_data(), input$acp_cat_vars, input$acp_vars, input$contrib_value)
  })
  
  output$acp_results_text <- renderPrint({
    req(reactive_acp$result)
    summary(reactive_acp$result)
  })
  
  # Choix d'axes
  output$acp_eigenvalues <- renderPlot({
    req(reactive_acp$result)
    
    # Extraction des valeurs propres
    valeurspropres <- reactive_acp$result$eig
    
    # Création du barplot
    barplot(valeurspropres[, 2], names.arg = 1:nrow(valeurspropres),
            main = "Pourcentage de la variance expliquée par chaque composante",
            xlab = "Composantes principales",
            ylab = "Pourcentage de variance expliquée",
            col = "steelblue")
    
    # Ajout de la ligne connectée
    lines(x = 1:nrow(valeurspropres), valeurspropres[, 2], 
          type = "b", pch = 19, col = "red")
  })
  
  # Graphique des contributions des variables à PC1
  output$contrib_PC1 <- renderPlot({
    req(reactive_acp$result)
    fviz_contrib(reactive_acp$result, choice = "var", axes = 1, top = 10)
  })
  
  # Graphique des contributions des variables à PC2
  output$contrib_PC2 <- renderPlot({
    req(reactive_acp$result)
    fviz_contrib(reactive_acp$result, choice = "var", axes = 2, top = 10)
  })
  
  # cos² a PC1
  output$cos2_PC1 <- renderPlot({
    req(reactive_acp$result)
    fviz_cos2(reactive_acp$result, choice = "var", axes = 1, top = 10) +
      ggtitle("Qualité de la représentation des variables sur la PC1 (cos²)")
  })
  
  # cos² a PC2
  output$cos2_PC2 <- renderPlot({
    req(reactive_acp$result)
    fviz_cos2(reactive_acp$result, choice = "var", axes = 2, top = 10) +
      ggtitle("Qualité de la représentation des variables sur la PC2 (cos²)")
  })
  
  # Matrice de covariance
  output$var_cov_matrix <- renderPrint({
    req(reactive_acp$selected_vars)
    print(get_S(filtered_data()[ , reactive_acp$selected_vars]))
  })
  
  output$eigen_values <- renderPrint({
    req(reactive_acp$selected_vars)
    
    # Récupération des valeurs propres
    lambdas <- get_LambdasAndEigenVectors(filtered_data()[, reactive_acp$selected_vars])$lambdas
    
    # Calcul du pourcentage de variance expliquée
    variance_percentage <- (lambdas / sum(lambdas)) * 100
    
    # Calcul du pourcentage de variance cumulée
    cumulative_variance <- cumsum(variance_percentage)
    
    # Création du tableau
    eigen_table <- data.frame(
      "eigenvalue" = lambdas,
      "percentage of variance" = variance_percentage,
      "cumulative percentage of variance" = cumulative_variance
    )
    
    print(eigen_table)
  })
  
  output$eigen_vectors <- renderPrint({
    req(reactive_acp$selected_vars)
    print(get_LambdasAndEigenVectors(filtered_data()[ , reactive_acp$selected_vars])$vectors)
  })
  
  output$inertia_percentage <- renderPrint({
    req(reactive_acp$selected_vars)
    print(get_InertiaAxes(filtered_data()[ , reactive_acp$selected_vars]))
  })
  
  # Sélectionne ou désélectionne toutes les variables pour l'ACP -----
  observeEvent(input$select_all_AC, {
    current_selection <- input$acp_vars  
    if (length(current_selection) < length(quant_vars_actives)) {
      updateSelectInput(session, "acp_vars", selected = quant_vars_actives)
    } else {
      updateSelectInput(session, "acp_vars", selected = character(0))
    }
  })
  
  # Génère une matrice de corrélation entre les variables sélectionnées -----
  output$corr_plot <- renderPlot({
    req(filtered_data(), input$corr_vars)  
    
    # Vérifie que les variables sélectionnées existent dans filtered_data() -----
    valid_vars <- intersect(input$corr_vars, colnames(filtered_data()))
    if (length(valid_vars) < 2) {
      plot.new()
      text(0.5, 0.5, "Veuillez sélectionner au moins deux variables valides", col = "red", cex = 1.5)
      return()
    }
    
    # Sélection des données quantitatives -----
    corr_data <- filtered_data()[, valid_vars, drop = FALSE]
    
    # Calcul de la matrice de corrélation -----
    corr_matrix <- cor(corr_data, use = "complete.obs")
    
    # Options de personnalisation (avec valeurs par défaut si non cochées) -----
    corr_method <- ifelse(input$customize_corr, input$corr_method, "circle")
    corr_type <- ifelse(input$customize_corr, input$corr_type, "full")
    corr_order <- ifelse(input$customize_corr, input$corr_order, "original")
    
    # Affichage de la matrice de corrélation -----
    corrplot(corr_matrix, method = corr_method, type = corr_type, order = corr_order,
             tl.cex = 0.8, cl.cex = 0.8)
  })
  
  # Reactive expression for the selected dataset
  df_select <- reactive({
    filtered_data()
  })
  
  
  # Filter data based on selected brand and year range
  filtered_evolution_data <- reactive({
    req(input$selected_brand, input$year_range)
    filtered_data() %>%
      filter(manufacturer == input$selected_brand & releaseYear >= input$year_range[1] & releaseYear <= input$year_range[2])
  })
  
  # Function to generate the evolution plot for a given characteristic
  generate_evolution_plot <- function(data, characteristic, brand) {
    ggplot(data, aes(x = releaseYear, y = !!sym(characteristic))) +
      geom_line() +
      labs(title = paste("Évolution de", characteristic, "pour", brand),
           x = "Année de sortie",
           y = "Valeur des caractéristiques") +
      theme_minimal() +
      scale_x_continuous(breaks = seq(min(data$releaseYear), max(data$releaseYear), by = 1)) +
      scale_y_continuous(breaks = seq(0, max(data[[characteristic]], na.rm = TRUE), by = 20))
  }
  
  # Generate the evolution plot for memClock
  output$evolution_plot_memClock <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memClock", input$selected_brand)
    ggplotly(p)
  })
  
  # Generate the evolution plot for unifiedShader
  output$evolution_plot_unifiedShader <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "unifiedShader", input$selected_brand)
    ggplotly(p)
  })
  
  # Generate the evolution plot for tmu
  output$evolution_plot_tmu <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "tmu", input$selected_brand)
    ggplotly(p)
  })
  
  # Generate the evolution plot for top
  output$evolution_plot_top <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "rop", input$selected_brand)
    ggplotly(p)
  })
  
  # Generate the evolution plot for memSize
  output$evolution_plot_memSize <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memSize", input$selected_brand)
    ggplotly(p)
  })
  
  # Generate the evolution plot for memBusWidth
  output$evolution_plot_memBusWidth <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memBusWidth", input$selected_brand)
    ggplotly(p)
  })
  
  # Generate the evolution plot for gpuClock
  output$evolution_plot_gpuClock <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "gpuClock", input$selected_brand)
    ggplotly(p)
    
  })
  
}

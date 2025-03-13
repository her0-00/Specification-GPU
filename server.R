server <- function(input, output, session) {
  
  
  
  # Sélectionner toutes les options dans les filtres
  observeEvent(input$select_all, {
    updateSelectInput(session, "IGP", selected = IGP)
    updateSelectInput(session, "Marque", selected = marque)
  })
  
  # Filtrer les données selon les choix de l'utilisateur
  filtered_data <- reactive({
    req(input$IGP, input$Marque)
    df %>%
      filter(igp %in% input$IGP, manufacturer %in% input$Marque)
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
    p <- ggplot(df, aes_string(x = input$var_quanti)) +
      geom_histogram(binwidth = 10, fill = "blue", color = "black", alpha = 0.7) +
      labs(
        title = paste("Histogramme de", input$var_quanti),
        x = input$var_quanti,
        y = "Fréquence"
      ) 
    ggplotly(p)  # Conversion en graphique interactif
  })
  
  #boxplot
  output$boxplot <- renderPlotly({
    req(input$var_quanti)  # Vérification qu'une variable quantitative est choisie
    
    # Création du boxplot
    p <- ggplot(df, aes_string(y = input$var_quanti)) +
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
  
  # Exécution de l'ACP -----
  observeEvent(input$run_acp, {
    if (!is.null(input$acp_vars) && length(input$acp_vars) > 1) {
      reactive_acp$selected_vars <- input$acp_vars
      reactive_acp$result <- doitPerformACP(df, input$acp_vars)
    } else {
      reactive_acp$result <- NULL
      reactive_acp$selected_vars <- NULL
    }
  })
  
  output$acp_ind_plot <- renderPlot({
    req(reactive_acp$result)  # Vérifier que l'ACP a bien été réalisée
    plot_acp_ind(reactive_acp$result, df, input$acp_cat_vars, input$contrib_value)
  })
  
  
  # Tracer les graphiques des variables
  output$acp_var_plot <- renderPlot({
    req(reactive_acp$result)  # S'assurer que l'ACP a bien été réalisée
    plot_acp_var(reactive_acp$result, input$acp_vars)
  })
  
  observeEvent(input$apply_cat, {
    update_acp(input, df)
  })
  
  output$biplot <- renderPlot({
    req(reactive_acp$result)  # Vérifier que l'ACP a bien été réalisée
    plot_acp_biplot(reactive_acp$result, df, input$acp_cat_vars, input$acp_vars,input$contrib_value)
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
  # matrice cov
  output$var_cov_matrix <- renderPrint({
    req(reactive_acp$selected_vars)
    print(get_S(df[ , reactive_acp$selected_vars]))
  })
  
  output$eigen_values <- renderPrint({
    req(reactive_acp$selected_vars)
    
    # Récupération des valeurs propres
    lambdas <- get_LambdasAndEigenVectors(df[, reactive_acp$selected_vars])$lambdas
    
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
    print(get_LambdasAndEigenVectors(df[ , reactive_acp$selected_vars])$vectors)
  })
  
  output$inertia_percentage <- renderPrint({
    req(reactive_acp$selected_vars)
    print(get_InertiaAxes(df[ , reactive_acp$selected_vars]))
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
    df
  })
  
  # Train and evaluate models
  observeEvent(input$train_model, {
    req(input$algo, input$target_var)
    data <- df_select()
    target_var <- input$target_var
    
    if (input$algo == "Random Forest") {
      model <- train_random_forest(data, target_var)
    } else if (input$algo == "SVM") {
      model <- train_svm(data, target_var)
    } else if (input$algo == "KNN") {
      req(input$k_value)
      k <- input$k_value
      model <- train_knn(data, target_var, k)
    } else if (input$algo == "K-means") {
      req(input$centers)
      centers <- input$centers
      model <- perform_kmeans(data, centers)
    }
    
    output$model_summary <- renderPrint({
      print(model)
    })
    
    if (input$algo == "KNN") {
      output$model_evaluation <- renderPrint({
        eval <- evaluate_knn(model, data, target_var)
        print(eval)
      })
    } else {
      output$model_evaluation <- renderPrint({
        print("Evaluation is not available for this model type.")
      })
    }
  })
  # Filter data based on selected brand and year range
  filtered_evolution_data <- reactive({
    req(input$selected_brand, input$year_range)
    df %>%
      filter(manufacturer == input$selected_brand & releaseYear >= input$year_range[1] & releaseYear <= input$year_range[2])
  })
  
  # Function to generate the evolution plot for a given characteristic
  generate_evolution_plot <- function(data, characteristic, brand, color) {
    ggplot(data, aes(x = releaseYear, y = !!sym(characteristic), color = I(color))) +
      geom_line() +
      labs(title = paste("Évolution de", characteristic, "pour", brand),
           x = "Année de sortie",
           y = "Valeur des caractéristiques") +
      theme_minimal() # +
      #scale_y_continuous(breaks = seq(0, max(data[[characteristic]], na.rm = TRUE), by = 20))
  }
  
  # Generate the evolution plot for memClock
  output$evolution_plot_memClock <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memClock", input$selected_brand,'blue')
    ggplotly(p)
  })
  
  # Generate the evolution plot for unifiedShader
  output$evolution_plot_unifiedShader <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "unifiedShader", input$selected_brand,'red')
    ggplotly(p)
  })
  
  # Generate the evolution plot for tmu
  output$evolution_plot_tmu <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "tmu", input$selected_brand,'gold')
    ggplotly(p)
  })
  
  # Generate the evolution plot for top
  output$evolution_plot_top <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "rop", input$selected_brand,'cyan')
    ggplotly(p)
  })
  
  # Generate the evolution plot for memSize
  output$evolution_plot_memSize <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memSize", input$selected_brand,'violet')
    ggplotly(p)
  })
  
  # Generate the evolution plot for memBusWidth
  output$evolution_plot_memBusWidth <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memBusWidth", input$selected_brand,'maroon')
    ggplotly(p)
  })
  
  # Generate the evolution plot for gpuClock
  output$evolution_plot_gpuClock <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "gpuClock", input$selected_brand,'green')
    ggplotly(p)
  })
}

  


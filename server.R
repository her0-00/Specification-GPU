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
  observeEvent(input$run_acp, {
    req(input$acp_vars)
    active_data <- filtered_data()[, input$acp_vars]
    acp_result <- PCA(active_data, graph = FALSE)
    
    # Plot des projections des individus
    output$acp_ind_plot <- renderPlot({
      fviz_pca_ind(acp_result, geom = "point") +
        labs(title = "Projection des individus")
    })
    
    # Plot des projections des variables
    output$acp_var_plot <- renderPlot({
      fviz_pca_var(acp_result) +
        labs(title = "Projection des variables")
    })
    
    # Résumé de l'ACP
    output$acp_results_text <- renderPrint({
      print(acp_result)
    })
    
    # BiPlot ACP
    output$biplot <- renderPlot({
      fviz_pca_biplot(acp_result, geom = c("point", "text"))
    })
    
    # Valeurs propres
    output$eigen_values <- renderPrint({
      print(acp_result$eig)
    })
    
    # Matrice des variances-covariances
    output$var_cov_matrix <- renderPrint({
      cov(as.matrix(active_data))
    })
  })
  
  # Étude technique : Contributions et cos²
  output$contrib_PC1 <- renderPlot({
    req(input$run_acp)
    fviz_contrib(acp_result, choice = "var", axes = 1) +
      labs(title = "Contributions variables - Axe 1")
  })
  
  output$contrib_PC2 <- renderPlot({
    req(input$run_acp)
    fviz_contrib(acp_result, choice = "var", axes = 2) +
      labs(title = "Contributions variables - Axe 2")
  })
  
  output$cos2_PC1 <- renderPlot({
    req(input$run_acp)
    fviz_cos2(acp_result, choice = "var", axes = 1) +
      labs(title = "Cos² des variables - Axe 1")
  })
  
  output$cos2_PC2 <- renderPlot({
    req(input$run_acp)
    fviz_cos2(acp_result, choice = "var", axes = 2) +
      labs(title = "Cos² des variables - Axe 2")
  })
}

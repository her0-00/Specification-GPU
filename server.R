server <- function(input, output, session) {
  
  # Sélectionner toutes les options dans les filtres
  
  
  # Filtrer les données selon les choix de l'utilisateur
  filtered_data <- reactive({
    req(input$IGP)
    
    df_filtered <- df %>%
      filter(igp %in% input$IGP)
    print(length(df))
    
    if (input$IGP == "Yes") {
      df_filtered <- df_filtered[, !(names(df_filtered) %in% c("memClock", "memType"))]
    }
    
    df_filtered
    
  })
  
  observe({
  df_data <- filtered_data()
  print(length(df_data))
  
  # Variables quantitatives (numériques)
  quant_vars <- names(df_data)[sapply(df_data, is.numeric)][2:8]
  
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
  
  # Création des listes pour les variables quantitatives et qualitatives en utilisant les données filtrées
  
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
    req(input$var_quanti1)  
    p <- ggplot(df, aes_string(x = input$var_quanti1)) +
      geom_histogram(binwidth = 10, fill = "blue", color = "black", alpha = 0.7) +
      labs(
        title = paste("Histogramme de", input$var_quanti1),
        x = input$var_quanti1,
        y = "Fréquence"
      ) 
    ggplotly(p)  # Conversion en graphique interactif
  })
  
  # boxplot
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
  
  # Répartition des types de mémoire (Pie Chart)
  output$Pie <- renderPlotly({
    req(input$var_quali2, input$var_quanti)
    
    # Filtrer les données pour supprimer les valeurs contenant 'gpuChip*' dans var_quali2
    df_mem <- df %>%
      filter(!grepl("gpuChip\\*", !!sym(input$var_quali2))) %>%  # Exclure les valeurs contenant 'gpuChip*'
      group_by(!!sym(input$var_quali2)) %>%
      summarise(value = sum(!!sym(input$var_quanti), na.rm = TRUE))
    
    plot_ly(df_mem, 
            labels = ~get(input$var_quali2),  
            values = ~value,                 
            type = "pie") %>%
      layout(title = paste("Répartition de", input$var_quanti, "par", input$var_quali2))
  })
  
  # Nuage de point
  output$scatter <- renderPlotly({
    req(input$var_quanti_x, input$var_quanti_y)
    
    plot_ly(df, 
            x = ~get(input$var_quanti_x), 
            y = ~get(input$var_quanti_y), 
            color = ~get(input$var_quali),
            type = "scatter",
            mode = "markers") %>%
      layout(title = paste("Corrélation entre", input$var_quanti_x, "et", input$var_quanti_y),
             xaxis = list(title = input$var_quanti_x),
             yaxis = list(title = input$var_quanti_y))
  })
  
  # barchart
  output$barplot <- renderPlotly({
    req(input$var_quali)
    
    # Filtrer les variables qualitatives indésirables (par exemple, "productName" et "igp")
    if (input$var_quali %in% c("productName", "igp")) {
      return(NULL)  # Si la variable sélectionnée est "productName" ou "igp", ne pas afficher le graphique
    }
    
    # Calcul du nombre d'occurrences pour chaque valeur de la variable qualitative
    df_bar <- df %>%
      group_by(!!sym(input$var_quali)) %>%
      summarise(value = n())  # Calcul du nombre d'occurrences pour chaque catégorie de la variable qualitative
    
    # Affichage du graphique
    plot_ly(df_bar, 
            x = ~get(input$var_quali),  # Variable qualitative sur l'axe des abscisses
            y = ~value,  # Le nombre d'occurrences sur l'axe des ordonnées
            type = "bar") %>%
      layout(title = paste(input$var_quali),
             xaxis = list(title = input$var_quali),
             yaxis = list(title = "Nombre d'occurrences"))
  })
  
  # Filtrer les données selon la marque et la plage d'années sélectionnées
  filtered_acp_data <- reactive({
    req(input$selected_brand, input$year_ranges)
    filtered_data() %>%
      filter(manufacturer == input$selected_brand, releaseYear >= input$year_ranges[1], releaseYear <= input$year_ranges[2])
  })
  
  
  # Sélectionne ou désélectionne toutes les variables pour l'ACP -----
  observeEvent(input$select_all_AC, {
    current_selection <- input$acp_vars 
    if (length(current_selection) < length(quant_vars)) {
      updateSelectInput(session, "acp_vars", selected = quant_vars)
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
      print("Nombre de ligne ")
      print(as.data.frame(filtered_acp_data()))
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
   
      
      # Perform clustering with the optimal number of clusters
      cl2 <- kmeans(x = df_ACP_1, centers = 5, nstart = 100)
      print("Clustering Result (cl2):")
      print(cl2)  # Print clustering result
      # Add cluster number to the filtered_acp_data
      filtered_acp_data$Cluster <- cl2$cluster
      
      # Display the updated filtered_acp_data in an interactive dataframe
      output$clustered_table <- renderDataTable({
        datatable(filtered_acp_data, options = list(
          pageLength = 10,
          scrollX = TRUE,
          dom = 'Bfrtip',
          buttons = c('copy', 'csv', 'excel')
        ))
      })
      # Plot the clusters
      output$cluster_plot <- renderPlot({
        fviz_cluster(cl2, geom = "point", data = df_ACP_1, label = rownames(filtered_acp_data)) +
          labs(title = "Clustering des individus en ACP",
               x = "PC1",
               y = "PC2")
      })
      #kPI
      output$kpiCluster <- renderTable({
        cluster_summary <- filtered_acp_data %>%
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
        
        cluster_summary
      })
      output$topCardsPerCluster <- renderTable({
        filtered_acp_data %>%                
          group_by(Cluster) %>%
          arrange(desc(memSize + gpuClock + unifiedShader)) %>%  # critère perf combiné
          slice(1:3) %>%
          select(Cluster, productName, manufacturer, memSize, gpuClock, unifiedShader)
      })
    } else {
      reactive_acp$result <- NULL
      reactive_acp$selected_vars <- NULL
    }
  })
  
  # In your server, add the renderValueBox functions to create the value boxes
  output$offre <- renderValueBox({
    valueBox(
      value =filtered_acp_data_summarise[filtered_acp_data_summarise$Profil_recommande == input$profil_gpu, ]$`Cartes dans ce cluster`,
      subtitle = "Offres",
      icon = icon("microchip"),
      color = "blue"
    )
  })
  
  output$vram_mean <- renderValueBox({
    valueBox(
      value =filtered_acp_data_summarise[filtered_acp_data_summarise$Profil_recommande == input$profil_gpu, ]$`Moyenne VRAM (Go)`,
      subtitle = "Moyenne VRAM (Go)",
      icon = icon("microchip"),
      color = "blue"
    )
  })
  
  output$gpu_clock_mean <- renderValueBox({
  valueBox(
    value = filtered_acp_data_summarise[filtered_acp_data_summarise$Profil_recommande == input$profil_gpu, ]$`Moyenne GPU Clock (MHz)`,
    subtitle = "Moyenne GPU Clock (MHz)",
    icon = icon("tachometer-alt"),
    color = "green"
  )
})
  
  output$mem_bus_width_mean <- renderValueBox({
    valueBox(
      value = filtered_acp_data_summarise[filtered_acp_data_summarise$Profil_recommande == input$profil_gpu, ]$`Moyenne memBusWidth (bits)`,
      subtitle = "Moyenne memBusWidth (bits)",
      icon = icon("memory"),
      color = "purple"
    )
  })
  
  output$unified_shader_mean <- renderValueBox({
    valueBox(
      value = filtered_acp_data_summarise[filtered_acp_data_summarise$Profil_recommande == input$profil_gpu, ]$`Moyenne unifiedShader`,
      subtitle = "Moyenne unifiedShader",
      icon = icon("project-diagram"),
      color = "yellow"
    )
  }) 
  
  output$mem_clock_mean <- renderValueBox({
    valueBox(
      value =filtered_acp_data_summarise[filtered_acp_data_summarise$Profil_recommande == input$profil_gpu, ]$`Moyenne memClock (MHz)`,
      subtitle = "Moyenne memClock (MHz)",
      icon = icon("clock"),
      color = "orange"
    )
  })
  
  # Met à jour le tableau en fonction du profil sélectionné
  output$gpu_recommande_table <- renderDataTable({
    req(input$profil_gpu)
    df_filtre <-  filtered_acp_data_[ filtered_acp_data_$Profil_recommande == input$profil_gpu, ]%>%select(manufacturer,productName,releaseYear)
    
    # Mise à jour des choix pour la carte à décrire
    updateSelectInput(session, "selected_card", choices = unique(df_filtre$productName))
    
    df_filtre
  })
  
  # Affichage de la fiche de la carte sélectionnée
  output$gpu_card_description <- renderUI({
    req(input$selected_card)
    selected_data <- filtered_acp_data_[filtered_acp_data_$productName == input$selected_card, ]
    if (nrow(selected_data) == 0) return(NULL)
    
    
    # Determine the image URL based on the manufacturer
    brand <- selected_data$manufacturer[1]
    image_url <- switch(as.character(brand),
                        "NVIDIA" = "/th.bing.com/th?q=Icone+3D+NVIDIA&w=120&h=120&c=1&rs=1&qlt=90&cb=1&dpr=1.5&pid=InlineBlock&mkt=fr-FR&cc=FR&setlang=fr&adlt=strict&t=1&mw=247",
                        "Intel" = "/th.bing.com/th/id/OIP.IvgIqk__5dbehwP11oyjpwHaE7?w=241&h=180&c=7&r=0&o=5&dpr=1.5&pid=1.7",
                        "AMD" = "/th.bing.com/th/id/OIP.iG_tTE-qFnB3gQTXLBH4IgHaHa?w=172&h=180&c=7&r=0&o=5&dpr=1.5&pid=1.7")  # Default to NULL if no match
    
    tags$div(
      style = "display: flex; justify-content: space-between; align-items: flex-start; padding: 20px; border: 1px solid #ddd; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1);",
      
      tags$div(
        style = "flex: 1; padding-right: 20px;",
        tags$h3(selected_data$productName[1], style = "margin-bottom: 10px;"),
        tags$p(strong("Marque : "), selected_data$manufacturer[1]),
        tags$p(strong("Année de sortie : "), selected_data$releaseYear[1]),
        tags$p(strong("Mémoire : "), paste0(selected_data$memSize[1], " Mo")),
        tags$p(strong("Type de mémoire : "), selected_data$memType[1]),
        tags$p(strong("Fréquence GPU : "), paste0(selected_data$gpuClock[1], " MHz")),
        tags$p(strong("Idéal pour : "), selected_data$Profil_recommande[1])
      ),
      
      if (!is.null(image_url)) {
        tags$img(
          src = file.path("https:/", image_url), 
          height = "200px", 
          style = "border-radius: 15px; box-shadow: 0 4px 10px rgba(0,0,0,0.2);margin-top: 20px;"
        )
      }
    )
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
    req(input$selected_brand2, input$year_range)
    filtered_data() %>%
      filter(manufacturer == input$selected_brand2)
  })
  
  generate_evolution_plot <- function(data, characteristic, brand) {
    # Regrouper les données par année et calculer le maximum de la caractéristique par année
    data_max_by_year <- data %>%
      group_by(releaseYear) %>%
      summarise(max_value = max(!!sym(characteristic), na.rm = TRUE))
    
  
    output$brand_logo <- renderUI({
      if (input$selected_brand == "NVIDIA") {
        img(src = "NVLogo_2D_H.jpg", height = "70px", width = "300px")
      } else if (input$selected_brand == "AMD") {
        img(src = "AMD.png", height = "90px", width = "300px")
      } else if (input$selected_brand == "Intel") {
        img(src = "Intel.png", height = "90px", width = "300px")
      } else {
        # Par défaut, afficher une image ou rien
        NULL
      }
    })
  # Tracer le graphique avec les valeurs maximales par année
  ggplot(data_max_by_year, aes(x = releaseYear, y = max_value)) +
    geom_line() +
    labs(title = paste("Évolution de", characteristic, "pour", brand),
         x = "Année de sortie",
         y = paste("Valeur maximale de", characteristic)) +
    theme_minimal() +
    scale_x_continuous(breaks = seq(min(data_max_by_year$releaseYear), max(data_max_by_year$releaseYear), by = 1)) +
    scale_y_continuous(breaks = seq(0, max(data_max_by_year$max_value, na.rm = TRUE), by = 20))
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
    p <- generate_evolution_plot(data, "unifiedShader", input$selected_brand2)
    ggplotly(p)
  })
  
  # Generate the evolution plot for tmu
  output$evolution_plot_tmu <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "tmu", input$selected_brand2)
    ggplotly(p)
  })
  
  # Generate the evolution plot for top
  output$evolution_plot_top <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "rop", input$selected_brand2)
    ggplotly(p)
  })
  
  # Generate the evolution plot for memSize
  output$evolution_plot_memSize <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memSize", input$selected_brand2)
    ggplotly(p)
  })
  
  # Generate the evolution plot for memBusWidth
  output$evolution_plot_memBusWidth <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "memBusWidth", input$selected_brand2)
    ggplotly(p)
  })
  
  # Generate the evolution plot for gpuClock
  output$evolution_plot_gpuClock <- renderPlotly({
    req(filtered_evolution_data())
    data <- filtered_evolution_data()
    p <- generate_evolution_plot(data, "gpuClock", input$selected_brand2)
    ggplotly(p)
    
  })
  
}

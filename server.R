
# Initiation du serveur -----
server <- function(input, output, session) {
  
  # Fonction pour tout sélectionner -----
  observeEvent(input$select_all, {
    updateSelectInput(session, "IGP", selected = IGP)
    updateSelectInput(session, "Marque", selected = marque)
  })
  
  # Filtrer les données selon les choix -----
  filtered_data <- reactive({
    req(input$IGP, input$Marque)
    df %>%
      filter(igp %in% input$IGP, manufacturer %in% input$Marque)
  })
  
  # Générer la table des données -----
  output$table <- renderDataTable({
    datatable(filtered_data(), options = list(
      pageLength = 9,
      scrollX = TRUE,
      scrollY = "50vh",  # Hauteur fixe pour activer le scroll
      deferRender = TRUE,
      scroller = TRUE,
      lengthMenu = c(9, 15, 20,as.integer(nrow(df)/8),as.integer(nrow(df)/4),as.integer(nrow(df)/2),as.integer(nrow(df)/2)+ as.integer(nrow(df)/8),as.integer(nrow(df)/2)+ as.integer(nrow(df)/4),nrow(df)), # Options pour le nombre de lignes par page
      paging = TRUE, # Assurez-vous que la pagination est activée
      initComplete = JS(
        "function(settings, json) {",
        "$('table').css({'color': 'white'});",
        "$('thead th').css({'color': 'white'});",
        "}"
      )
    )) %>%
      formatStyle(
        columns = colnames(filtered_data()),
        color = 'white'
      )
  })
  
  # Générer les statistiques descriptives -----
  output$desc_stats <- renderDataTable({
    desc_stats <- skim(filtered_data()) %>%
      dplyr::select(skim_type, skim_variable, n_missing, complete_rate, factor.top_counts, numeric.mean, numeric.sd, numeric.p0, numeric.p25, numeric.p50, numeric.p75, numeric.p100)
    
    datatable(desc_stats, options = list(
      paging=FALSE,
      # Options pour le nombre de lignes par page
      initComplete = JS(
        "function(settings, json) {",
        "$('table').css({'color': 'white'});",
        "$('thead th').css({'color': 'white'});",
        "}"
      )
    )) %>%
      formatStyle(
        columns = colnames(desc_stats),
        color = 'white'
      )
  })
  
  # Télécharger les données -----
  output$downloadData <- downloadHandler(
    filename = function() {
      paste("data-", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(filtered_data(), file)
    }
  )
  # Télécharger les données -----
  output$downloadData2 <- downloadHandler(
    filename = function() {
      paste("datadesc-", Sys.Date(), ".csv", sep = "")
    },
    content = function(file) {
      write.csv(skim(filtered_data()), file)
    }
  )
}


# Initiation de l'UI -----
ui <- shinyUI(dashboardPage(
  dashboardHeader(title = "Caractérisation des GPU"),
  
  # Contenu de la barre latérale ------
  dashboardSidebar(
    sidebarMenu(
      menuItem("Présentation des données", tabName = "presentation", icon = icon("table")),
      menuItem("Analyses descriptives", tabName = "resume", icon = icon("file-alt")),
      menuItem("GPU PC", tabName = "GPUP", icon = icon("chart-bar")),
      menuItem("GPU laptop", tabName = "GPUL", icon = icon("chart-bar"))
    ),
    selectInput(
      inputId = "IGP",
      label = "IGP ? :",
      choices = IGP,
      selected = IGP,
      multiple = TRUE
    ),
    selectInput(
      inputId = "Marque",
      label = "Marque ? :",
      choices = marque,
      selected = marque,
      multiple = TRUE
    ),
    actionButton("select_all", "Tout sélectionner"),
    actionButton("apply_filters", "Rafraîchir"),
    
    # Ajout de mon nom et descriptif -----
    br(),
    div(style = "margin-top: 20px; padding: 10px; border-radius: 5px; text-align: center;",
        h4(style = "font-size: 16px;", "Développé par Nathan Avenel | Anas Ibnouali | Yénam Dossou"),
        p(style = "font-size: 13px;", "Étudiants en science des données"),
        p(style = "font-size: 13px;", "à l'IUT de Vannes")
    )
  ),
  
  # Contenu du corps -----
  dashboardBody(
    tags$head(
      tags$link(rel = "stylesheet", type = "text/css", href = "www/styles.css"),
      tags$style(HTML("
        body, .content-wrapper, .main-header, .main-sidebar {
          font-family: 'Times New Roman', Times, serif;
          background-color: #808080; /* Fond gris */
          color: #ffffff;
        }
        .skin-blue .main-header .box {
          background-color: #696969;
        }
        .skin-blue .main-header .navbar {
          background-color: #696969;
        }
        .skin-blue .main-header .logo {
          background-color: #696969;
          color: #ffffff;
          border-bottom: 0 solid transparent;
        }
        .skin-blue .main-header .logo:hover {
          background-color: #696969;
        }
        .skin-blue .main-sidebar {
          background-color: #696969;
        }
        .skin-blue .main-sidebar .sidebar .sidebar-menu .active a {
          background-color: #808080;
        }
        .skin-blue .main-sidebar .sidebar .sidebar-menu a {
          background-color: #696969;
          color: #ffffff;
        }
        .skin-blue .main-sidebar .sidebar .sidebar-menu a:hover {
          background-color: #808080;
        }
        .skin-blue .main-header .navbar .sidebar-toggle {
          color: #ffffff;
        }
        .skin-blue .main-header .navbar .sidebar-toggle:hover {
          background-color: #808080;
        }
        .centered {
          text-align: center;
        }
        .box-centered {
          display: flex;
          justify-content: center;
        }
        .input-centered {
          display: flex;
          justify-content: center;
          align-items: center;
        }
        .box-centered {
          display: flex;
          justify-content: center;
        }
        .descriptive-text {
          padding: 20px;
          border-radius: 10px;
          background: linear-gradient(to right, black, grey);
        }
        .boxplot-box {
          color: white;
        }
        .box {
          background: linear-gradient(to right, black, grey);
        }
        .box-primary {
          background-color: grey !important;
        }
      "))
    ),
    tabItems(
      # Première section : Présentation des données -----
      tabItem(tabName = "presentation",
              fluidRow(
                column(12,
                       box(
                         title = "Descriptif des données",
                         status = "primary",
                         solidHeader = TRUE,
                         width = NULL,
                         p("On s'intéresse aux GPU")
                       )
                )
              ),
              fluidRow(
                column(12,
                       box(
                         title = "Tableau des données",
                         status = "primary",
                         solidHeader = TRUE,
                         width = NULL,
                         dataTableOutput("table"),
                         downloadButton("downloadData", "Télécharger les données")
                       )
                )
              )
      ),
      
      # Deuxième section : Analyses descriptives -----
      tabItem(tabName = "resume",
              fluidRow(
                h2("Analyse des données", class = "centered"),
                tabsetPanel(
                  # Onglet des valeurs manquantes
                  tabPanel("Valeurs manquantes",
                           fluidRow(
                             column(12,
                                    box(
                                      title = "Analyses descriptives",
                                      status = "primary",
                                      solidHeader = TRUE,
                                      width = NULL,
                                      dataTableOutput("desc_stats"),
                                      downloadButton("downloadData2", "Télécharger les données")
                                    )
                             )
                           )
                  ),
                  # Onglet des visualisations
                  tabPanel("Visualisation",
                           fluidRow(
                             column(6,
                                    selectInput(
                                      inputId = "var_quanti",
                                      label = "Choisissez une variable quantitative :",
                                      choices = quant_vars,  # Liste des variables quantitatives
                                      selected = quant_vars[1]
                                    ),
                                    plotOutput("histogram")
                             ),
                             column(6,
                                    selectInput(
                                      inputId = "var_quali",
                                      label = "Choisissez une variable qualitative :",
                                      choices = names(df)[sapply(df, is.factor)],  # Liste des variables qualitatives
                                      selected = names(df)[sapply(df, is.factor)][1]
                                    ),
                                    dataTableOutput("qualitative_table")
                             )
                           )
                  )
                )
              )
      )
    )
  )
))

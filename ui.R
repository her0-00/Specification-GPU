# Initiation de l'UI -----
ui <- shinyUI(dashboardPage(
  dashboardHeader(title = "Caractérisation des GPU"),
  
  # Contenu de la barre latérale ------
  dashboardSidebar(
    sidebarMenu(
      menuItem("Présentation des données", tabName = "presentation", icon = icon("table")),
      menuItem("Visualisations des données ", tabName = "resume", icon = icon("file-alt")),
      menuItem("ACP", tabName = "acp", icon = icon("chart-line")),
      menuItem("Etude Technique", tabName = "Etude_technique", icon = icon("cogs")),
      menuItem("Matrice de Corrélation", tabName = "correlation", icon = icon("th")),
      menuItem("Évolution des GPU", tabName = "evolution", icon = icon("line-chart")),
      menuItem("Choix du GPU adapté", tabName = "choix_gpu", icon = icon("microchip"))
    ),
    selectInput(
      inputId = "IGP",
      label = "IGP ? :",
      choices = IGP,
      selected = IGP[1],
      multiple = FALSE
    ),
    
    
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
    useShinyjs(),
    
    tags$head(
      tags$style(HTML(
        "body {font-family: 'Arial', sans-serif; background-color: #F4F6F9; color: #333;}
         
         .skin-blue .main-header .logo, .skin-blue .main-header .navbar { background-color: #3271a5; }
         .skin-blue .main-sidebar { background-color: #3271a5; }
         .box { border-radius: 12px; box-shadow: 3px 3px 15px rgba(0, 0, 0, 0.15); transition: 0.3s ease-in-out; }
         .box:hover { transform: none !important ; }
         .btn { transition: background-color 0.3s ease-in-out, box-shadow 0.3s ease-in-out; border-radius: 8px; }
         .btn:hover { background-color: #ff9800 !important; color: white !important; box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3); }
         .dark-mode { background-color: #2C3E50; color: white; }
         .dark-mode .box { background-color: #34495E; color: white; border-color: #555; }
         .dark-mode .btn { background-color: #5DADE2 !important; color: white !important; }
         .dark-mode .sidebar { background-color: #1A252F !important; }
         .dark-mode .main-header, .dark-mode .navbar { background-color: #1F2933; }
         .dark-mode .sidebar-menu > li > a { color: white !important; }
         .dark-mode .sidebar-menu > li.active > a { background-color: #445A6F !important; }
         .tab-pane { padding: 15px; }
         .box-body { padding: 15px; }
         .footer { background-color: #222D32; color: white; padding: 15px; text-align: center; font-size: 14px; }
         .nav-tabs-custom .nav-tabs li a {
      font-size: 15px;
      font-weight: bold;
      color: #3271a5;
      padding: 10px 15px;
      border-radius: 8px;
      transition: all 0.3s ease-in-out;
    }
    
    .nav-tabs-custom .nav-tabs li a:hover {
      background-color: #ff9800;
      color: white !important;
      border-radius: 8px;
    }

    .nav-tabs-custom .nav-tabs .active a, 
    .nav-tabs-custom .nav-tabs .active a:hover {
      background-color: #3271a5 !important;
      color: white !important;
      border-radius: 8px;
    }

    .nav-tabs {
      border-bottom: 2px solid #3271a5;
      margin-bottom: 15px;
    }
        /* Style général des onglets */
    .nav-tabs-custom .nav-tabs li a {
      font-size: 16px;
      font-weight: bold;
      color: #3271a5;
      padding: 12px 18px;
      border-radius: 8px;
      transition: all 0.3s ease-in-out;
      text-transform: uppercase;
      letter-spacing: 1px;
    }


    /* Style de l'onglet actif */
    .nav-tabs-custom .nav-tabs .active a, 
    .nav-tabs-custom .nav-tabs .active a:hover {
      background-color: #3271a5 !important;
      color: white !important;
      border-radius: 8px;
      box-shadow: 0px 4px 10px rgba(0, 0, 0, 0.3);
      position: relative;
    }
      
    .selectize-dropdown {
      z-index: 10000 !important; /* S'assure que la liste est bien au-dessus */
      position: absolute !important; /* Fixe la position */
    }
    
    
    .selectize-dropdown-content {
      position: relative !important; /* Empêche le flottement de la liste */
    }
    
    .box {
      overflow: visible !important; /* S'assure que la box ne cache pas la liste */
    }
    
    .selectize-input {
      cursor: pointer !important; /* Améliore la sélection */
    }


        "
      ))
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
                         p("Les unités de traitement graphique (GPU) sont essentielles dans l'informatique moderne, ayant évolué des simples accélérateurs graphiques pour jeux vidéo à des composants clés dans l'intelligence artificielle, le calcul scientifique et le traitement de données massives. Leur capacité à traiter des milliers de threads simultanément permet des applications variées, telles que l'entraînement rapide des réseaux de neurones et la réalisation de simulations complexes. Bien que puissants et efficaces, les GPU posent des défis en matière de programmation et d'optimisation, nécessitant une expertise spécifique pour maximiser leur potentiel. L'étude des GPU est donc cruciale pour comprendre leur impact technologique et leur avenir prometteur.
")
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
                # Onglet des visualisations
                tabPanel("Visualisation",box(
                  fluidRow(
                    column(12,
                           selectInput(
                             inputId = "var_quanti1",
                             label = "Choisissez une variable quantitative :",
                             choices = setdiff(quant_vars, c("releaseYear")),  # Liste des variables quantitatives
                             selected = "memeSize")
                    ))
                  
                  ,
                  fluidRow(
                    column(12,
                           plotlyOutput("histogram"))))
                  
                  
                  ,
                  
                  box(
                    fluidRow(
                      column(12,
                             selectInput(
                               inputId = "var_quanti",
                               label = "Choisissez une variable quantitative :",
                               choices = setdiff(quant_vars, c("releaseYear")),  # Liste des variables quantitatives
                               selected = "memeSize")
                      ),
                      column(12,plotlyOutput("boxplot")))),
                  
                  box(height = "600px",
                      column(12,
                             # Sélection des variables X et Y pour le Scatter Plot
                             selectInput("var_quanti_x", "Variable X (Scatter Plot) :", 
                                         choices = setdiff(quant_vars, c("productName","releaseYear")),
                                         selected = "gpuClock"),
                             selectInput("var_quanti_y", "Variable Y (Scatter Plot) :", 
                                         choices = setdiff(quant_vars, c("productName","releaseYear")),
                                         selected = "memClock"),
                             column(12,plotlyOutput("scatter"))
                      )),
                  
                  box(height = "600px",
                      fluidRow(
                        column(12,
                               selectInput(
                                 inputId = "var_quali",
                                 label = "Choisissez une variable qualitative :",
                                 choices = setdiff(names(df)[sapply(df, is.factor)], c("productName", "igp")),  # Liste des variables qualitatives
                                 selected = names(df)[sapply(df, is.factor)][1]
                                 
                               ))),
                      fluidRow(
                        column(12,
                               plotlyOutput("barplot"))))
                  
                  ,
                  box(width = 12 , height = "700px",
                      fluidRow(
                        column(12,
                               selectInput(
                                 inputId = "var_quali2",
                                 label = "Choisissez une variable qualitative :",
                                 choices = setdiff(qual_vars, c("productName","igp","gpuChip")),  # Liste des variables qualitatives
                                 selected = "memType"
                                 
                               ))
                        ,column(12,plotlyOutput("Pie", height = "500px"))
                        
                      )
                  ),
                  
                  
                )
                
                
                
              )
      ),
      
      # Onglet ACP
      tabItem(tabName = "acp",
              tabsetPanel(
                tabPanel("Affichage des projections",
                         fluidRow(
                           box(
                             title = "Sélectionnez les variables pour l'ACP", status = "primary", solidHeader = TRUE, width = 12,
                             #selectInput("acp_vars", "Variables actives :", choices = quant_vars_actives, selected = quant_vars_actives[1:3], multiple = TRUE),
                             selectInput( "acp_vars", "Variables actives :", choices =quant_vars,multiple = TRUE ),
                             selectInput("selected_brand", "Choix de la marque:", choices = marq_, selected = marq_, multiple = TRUE),
                             sliderInput("year_ranges", "Sélectionnez la plage d'années :", min = min_year, max = max_year, value = c(min_year, max_year)),
                             numericInput("contrib_value", "Valeur de contrib :", value = 50, min = 10, max = 100),
                             actionButton("run_acp", "Lancer l'ACP", class = "btn-success"),
                             actionButton("select_all_AC", "Sélectionner toutes les variables", class = "btn-info")
                           )
                         ),
                         
                         fluidRow( 
                           column(6, box(title = "Projection des individus", status = "primary", solidHeader = TRUE, width = 12, plotOutput("acp_ind_plot"))),
                           column(6, box(title = "Clustered Data", status = "primary", solidHeader = TRUE, width = 12, plotOutput("nb_clust"))),
                           column(6, box(title = "Clustered Data", status = "primary", solidHeader = TRUE, width = 12, plotOutput("cluster_plot")
                           )),
                           column(6, box(title = "Projection des variables", status = "primary", solidHeader = TRUE, width = 12, plotOutput("acp_var_plot"))),
                           # column(6, box(title = "Résumé de l'ACP", status = "primary", solidHeader = TRUE, width = 12, verbatimTextOutput("acp_results_text"))),
                           #column(6, box(title = "BiPlot", status = "primary", solidHeader = TRUE, width = 12, plotOutput("biplot"))),
                           column(12,box(title='Data', status = "primary", solidHeader = TRUE, width = 12,dataTableOutput("clustered_table")))
                         )
                ),
                tabPanel("KPI des Clusters GPU",
                         fluidPage(
                           h2("Indicateurs de performance par cluster"),
                           tableOutput("kpiCluster"),
                           br(),
                           h3("Cartes graphiques les plus performantes par cluster"),
                           tableOutput("topCardsPerCluster"),
                           br(),
                           h3("Recommandations d’usage par cluster"),
                           tableOutput("clusterMeaning")
                         )
                )
                ,
                
                tabPanel("Choix du nombre d'axes factorielles",
                         box(title = "Choix du nombre d'axes factorielles", status = "primary", solidHeader = TRUE, width = 12,
                             plotOutput("acp_eigenvalues"))
                ),
                tabPanel("Matrice des variances-covariances",
                         box(title = "Matrice des variances-covariances", status = "primary", solidHeader = TRUE, width = 12,
                             verbatimTextOutput("var_cov_matrix"))
                ),
                tabPanel("Valeurs propres",
                         box(title = "Valeurs propres", status = "primary", solidHeader = TRUE, width = 12,
                             verbatimTextOutput("eigen_values"))
                ),
                tabPanel("Vecteurs Propres",
                         box(title = "Vecteurs propres", status = "primary", solidHeader = TRUE, width = 12,
                             verbatimTextOutput("eigen_vectors"))
                )
                
                
              )
              
      ),
      
      # Onglet Étude Technique
      tabItem(tabName = "Etude_technique",
              tabsetPanel(
                tabPanel("Contributions des variables",
                         fluidRow(
                           box(title = "Axe 1", status = "primary", solidHeader = TRUE, width = 12,
                               plotOutput("contrib_PC1"))
                         ),
                         fluidRow(
                           box(title = "Axe 2", status = "primary", solidHeader = TRUE, width = 12,
                               plotOutput("contrib_PC2"))     
                         )
                ),
                tabPanel("Qualité de la représentation des variables (cos²)",
                         fluidRow(
                           box(title = "Axe 1", status = "primary", solidHeader = TRUE, width = 12,
                               plotOutput("cos2_PC1"))
                         ),
                         fluidRow(
                           box(title = "Axe 2", status = "primary", solidHeader = TRUE, width = 12,
                               plotOutput("cos2_PC2"))
                         )
                )
              )
      ), # Fin de l'onglet Étude Technique
      
      # Onglet affichant la matrice de corrélation -----
      tabItem(tabName = "correlation",
              fluidRow(
                box(
                  title = "Sélectionnez les variables", status = "primary", solidHeader = TRUE, width = 12,
                  selectInput("corr_vars", "Sélectionnez les variables :", 
                              choices = quant_vars, 
                              selected = quant_vars[1:2], 
                              multiple = TRUE),
                  actionButton("select_all_corr", "Sélectionner toutes les variables", class = "btn-info")
                ),
                box(title = "Options de personnalisation", status = "primary", solidHeader = TRUE, width = 12,
                    checkboxInput("customize_corr", label=tags$span(style = "color: black;", "Personnaliser l'apparence"), value = FALSE),
                    conditionalPanel(
                      condition = "input.customize_corr == true",
                      selectInput("corr_method", label=tags$span(style = "color: black;", "Méthode de corrélation"), 
                                  choices = c("circle", "square", "color", "number"), selected = "circle"),
                      selectInput("corr_type", label=tags$span(style = "color: black;", "Type de matrice"), 
                                  choices = c("full", "upper", "lower"), selected = "full"),
                      selectInput("corr_order", label=tags$span(style = "color: black;", "Ordre des variables"), 
                                  choices = c("original", "alphabet", "hclust"), selected = "original")
                    )
                ),
                box(title = "Matrice de Corrélation", status = "primary", solidHeader = TRUE, width = 12, plotOutput("corr_plot"))
              )
      ),
      
      
      tabItem(tabName = "evolution",
              fluidRow(box(
                       column(6,
                              selectInput("selected_brand2", "Sélectionnez la marque :", choices = unique(df$manufacturer), selected = unique(df$manufacturer)[1])
                       ),
                       column(4, uiOutput("brand_logo")))
              
    )
,
  fluidRow( column(12,box(title = "Mémoire (memSize)", status = "primary", solidHeader = TRUE, width = 12, plotlyOutput("evolution_plot_memSize"))),
  column(12, box(title = "Bus de mémoire (memBusWidth)", status = "primary", solidHeader = TRUE, width = 12, plotlyOutput("evolution_plot_memBusWidth"))),
  column(12,box(title = "Shader Unifié (unifiedShader)", status = "primary", solidHeader = TRUE, width = 12, plotlyOutput("evolution_plot_unifiedShader"))),
column(12, box(title = "TMU", status = "primary", solidHeader = TRUE, width = 12, plotlyOutput("evolution_plot_tmu"))),
column(12, box(title = "rop", status = "primary", solidHeader = TRUE, width = 12, plotlyOutput("evolution_plot_top")))
)
),
      # Onglet Choix du GPU adapté -----
      tabItem(tabName = "choix_gpu",
              fluidRow(
                box(title = "Sélection du domaine",
                    status = "primary",
                    solidHeader = TRUE,
                    width = 12,
                    selectInput("profil_gpu", "Choisissez un domaine possible parmi la liste :", 
                                choices = unique(filtered_acp_data_$Profil_recommande),
                                selected = unique(filtered_acp_data_$Profil_recommande)[1])
                )
              ),
              fluidRow(
                valueBoxOutput("offre"),
                valueBoxOutput("vram_mean"),
                valueBoxOutput("gpu_clock_mean"),
                valueBoxOutput("mem_bus_width_mean"),
                valueBoxOutput("unified_shader_mean"),
                valueBoxOutput("mem_clock_mean"),
                valueBoxOutput("profile_recommendation")
              )
              ,
              fluidRow(
                box(title = "Cartes graphiques recommandées",
                    status = "primary",
                    solidHeader = TRUE,
                    width = 12,
                    dataTableOutput("gpu_recommande_table")
                )
              ),
              
              fluidRow(
                box(title = "Fiche descriptive de la carte sélectionnée",
                    status = "primary",
                    solidHeader = TRUE,
                    width = 12,
                    selectInput("selected_card", "Choisissez une carte :", 
                                choices = NULL),
                    uiOutput("gpu_card_description")
                )
              )
      )
      
    )
  )
)
)

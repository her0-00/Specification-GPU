library(shiny)
library(tidyverse)
library(FactoMineR)
library(Factoshiny)

### PREPA DU DATAFRAME DATA ###

data = read_csv2("data/gpu_specs_v7.csv")
active <- data[,c(4:12)]
data$memSize = as.numeric(data$memSize)
data$releaseYear = as.factor(data$releaseYear)
data$manufacturer = as.factor(data$manufacturer)

data <- data %>%
  filter(manufacturer %in% c("AMD", "NVIDIA", "Intel")) %>%
  mutate(memBusWidth = ifelse(is.na(memBusWidth), memSize * 16, memBusWidth)) %>%
  filter(!is.na(releaseYear))




### PARTIE SEPARATION ###

CG_PC <- data %>% filter(
  (is.na(vertexShader) | vertexShader == "") &
    (is.na(pixelShader) | pixelShader == "") &
    igp == "No"
)

CG_PC <- CG_PC %>% select(
  -pixelShader, 
  -vertexShader
)

sum(is.na(CG_PC))
print(CG_PC)

### PARTIE IGPU ###

CG_IGPU <- data %>%
  filter(igp == "Yes")

CG_IGPU <- CG_IGPU %>% select(
  -pixelShader, 
  -vertexShader,
  -memType,
  -memClock) %>%
  filter(!is.na(unifiedShader) & unifiedShader != "")



sum(is.na(CG_IGPU))

### PARTIE CONCATENATION ###

CG_ALL <- bind_rows(CG_PC, CG_IGPU)


# Sauvegarder les sous-ensembles dans des fichiers CSV séparés
write.csv(CG_PC, "data/CG_PC.csv", row.names = FALSE)
write.csv(CG_IGPU, "data/CG_IGPU.csv", row.names = FALSE)
write.csv(CG_ALL, "data/CG_ALL.csv", row.names = FALSE)



MAIN='D:/onpe_scrapper/Data/last_review'
librarian::shelf(
  sf, tidyverse, scales, patchwork
)
theme_set(theme_minimal())

map_na=st_read(paste0(MAIN, '/1.geojson'))
map_e=st_read(paste0(MAIN, '/2.geojson'))
result_data = read_csv(paste0(MAIN, '/last_results.csv'))

f07 <- "D:/onpe_scrapper/data/last_review/geometry/prov/ambito=1/070900.geojson" |> st_read()
f12 <- "D:/onpe_scrapper/data/last_review/geometry/prov/ambito=1/120100.geojson" |> st_read()
f17 <- "D:/onpe_scrapper/data/last_review/geometry/prov/ambito=1/170100.geojson" |> st_read()
map_nacional <- bind_rows(map_na, f07, f12, f17) |> 
  st_as_sf() |> 
  select(ID, id) |> 
  mutate(ambito = 1, type = 'nacion') |> 
  rename(ubigeo = ID) |> st_as_sf()

map_ext <- map_e |>
  st_make_valid() |>
  mutate(
    ambito = 2,
    prov_ubigeo = if_else(str_detect(id, "^\\d+$"), id, NA_character_)
  ) |>
  group_by(prov_ubigeo) |>
  summarise(
    geometry = st_union(geometry),
    country = first(name),
    contineent = first(Continent),
    .groups = "drop"
  )

# colores representativos por partido
party_colors <- c("JP" = "#1B7A3D", "FP" = "#FF7F00")

# ---- sobre el 50% (distrital / nacional) ----
df_50 <- result_data |> 
  mutate(
    ambito = ifelse(dep_ubigeo %in% c('140000', '240000'), 0, ambito)
    # ambito: 0 lima callao, 1 resto del peru, 2 extranjero
  ) |> 
  group_by(ubigeo) |> 
  mutate(
    sum_total_votos_validos = sum(total_votos_validos)
  ) |> 
  filter(porcentaje_votos_validos >= 50) |>
  arrange(desc(porcentaje_votos_validos)) |> 
  slice(1) |> 
  group_by(ambito) |> 
  mutate(p_total_votos = sum_total_votos_validos / sum(sum_total_votos_validos)) |> 
  mutate(diff_50 = porcentaje_votos_validos - 50) |> 
  ungroup() |> 
  mutate(
    ambito_label = case_when(
      ambito == 0 ~ "Lima y Callao",
      ambito == 1 ~ "Resto del Perú",
      ambito == 2 ~ "Extranjero"
    ),
    fill = case_when(
      partido == "JP" ~ col_numeric(c("white", "#1B7A3D"), domain = c(0, 50))(pmin(diff_50, 50)),
      partido == "FP" ~ col_numeric(c("white", "#FF7F00"), domain = c(0, 50))(pmin(diff_50, 50))
    )
  )

# =========================================================
# HISTOGRAMAS — 3 gráficos separados: Lima/Callao, Perú, Extranjero
# =========================================================

plot_hist <- function(data, titulo, b = 20) {
  ggplot(data) +
    geom_histogram(aes(x = diff_50, fill = partido), alpha = .75, bins = b) +
    facet_wrap(~partido, ncol = 1) +
    scale_fill_manual(values = party_colors, guide = "none") +
    labs(y = '', x = '% sobre el 50%', title = titulo)
}

hist_lima <- plot_hist(df_50 |> filter(ambito == 0), "Lima y Callao — % sobre el 50% (distrital)")
hist_peru <- plot_hist(df_50 |> filter(ambito == 1), "Resto del Perú — % sobre el 50% (distrital)",)
hist_ext  <- plot_hist(df_50 |> filter(ambito == 2), "Extranjero — % sobre el 50% (a nivel país)")

hist_lima
hist_peru
hist_ext

# =========================================================
# MAPAS — 3 mapas (Lima/Callao, Perú, Extranjero), cada uno
# con 2 paneles: diferencia sobre el 50% | representación de votos
# =========================================================

df_map_lima <- df_50 |> 
  filter(ambito == 0) |> 
  left_join(map_nacional, by = "ubigeo") |> 
  st_as_sf() |> 
  st_make_valid()

df_map_peru <- df_50 |> 
  filter(ambito == 1) |> 
  left_join(map_nacional, by = "ubigeo") |> 
  st_as_sf() |> 
  st_make_valid()

# extranjero: se agrupa a nivel pais (no hay geometria a nivel estado/dpto)
df_map_ext_data <-
  result_data |>
  filter(ambito == 2) |> 
  group_by(dep_ubigeo, prov_ubigeo, partido) |> 
  summarise(total_votos_validos = sum(total_votos_validos), .groups = "drop") |> 
  group_by(dep_ubigeo, prov_ubigeo) |> 
  mutate(
    sum_total_votos_validos = sum(total_votos_validos),
    p_total = total_votos_validos / sum_total_votos_validos, 
    diff_50 = p_total * 100 - 50
  ) |> 
  filter(p_total >= .5) |> 
  group_by(prov_ubigeo) |> 
  slice(1) |> 
  ungroup() |> 
  mutate(p_total_votos = sum_total_votos_validos / sum(sum_total_votos_validos)) |> 
  mutate(
    fill = case_when(
      partido == "JP" ~ col_numeric(c("white", "#1B7A3D"), domain = c(0, 50))(pmin(diff_50, 50)),
      partido == "FP" ~ col_numeric(c("white", "#FF7F00"), domain = c(0, 50))(pmin(diff_50, 50))
    )
  )

df_map_ext <- df_map_ext_data |> 
  full_join(map_ext, by = "prov_ubigeo") |> 
  st_as_sf() |> 
  st_make_valid()

# --- funciones de graficado ---

map_diff_50 <- function(data, titulo, border = NA) {
  ggplot(data) +
    geom_sf(aes(fill = fill), color = border) +
    scale_fill_identity(na.value = "grey90") +
    coord_sf() +
    theme_void() +
    labs(title = paste0(titulo, "\nDiferencia sobre el 50%"))
}

map_p_total <- function(data, titulo, border = NA) {
  ggplot(data) +
    geom_sf(aes(fill = p_total_votos), color = border) +
    scale_fill_distiller(
      name = "% votos\nen el ámbito",
      palette = "YlOrRd",
      direction = 1,        # 1 = claro (bajo) -> oscuro (alto)
      labels = percent,
      na.value = "grey90"
    ) +
    coord_sf() +
    theme_void() +
    labs(title = paste0(titulo, "\nRepresentación de votos"))
}

combo_map <- function(data, titulo, border = NA) {
  map_diff_50(data, titulo, border) | map_p_total(data, titulo, border)
}

combo_lima <- combo_map(df_map_lima, "Lima y Callao")
combo_peru <- combo_map(df_map_peru, "Resto del Perú")
combo_ext  <- combo_map(df_map_ext,  "Extranjero", border = "grey70")

combo_lima
combo_peru
combo_ext
map_diff_50(df_map_ext, 'Extranjero', border = "grey70")

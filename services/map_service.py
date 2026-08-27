"""
Serviço de Renderização Geoespacial (Módulo do Mapa)
Responsável exclusivamente por carregar, processar e renderizar as geometrias
de linhas e pontos dos empreendimentos no mapa interativo (Folium).
"""

import html as html_mod
import pandas as pd
import streamlit as st
import folium
from streamlit_folium import folium_static
from shapely import wkt
from services import data_loader


def get_combined_bounds(geometries):
    """Calcula a bounding box envolvente para uma lista de geometrias Shapely."""
    min_x, min_y, max_x, max_y = float("inf"), float("inf"), float("-inf"), float("-inf")
    for g in geometries:
        if g is not None and not g.is_empty:
            b = g.bounds
            min_x = min(min_x, b[0])
            min_y = min(min_y, b[1])
            max_x = max(max_x, b[2])
            max_y = max(max_y, b[3])
    return min_x, min_y, max_x, max_y


def render_map(empreendimento_id):
    """
    Renderiza o mapa interativo do empreendimento utilizando Folium.
    Exibe intervenções lineares (linhas) e intervenções pontuais (pontos).
    Utiliza OpenStreetMap como mapa base (100% gratuito, aberto e sem necessidade de chave de API).
    """
    df_geo = data_loader.get_empreendimento_geo()

    if df_geo.empty:
        _render_no_geometry_placeholder("Base de dados geoespaciais não disponível.")
        return

    # Busca o registro geoespacial do empreendimento com conversão defensiva
    emp_id_num = pd.to_numeric(empreendimento_id, errors="coerce")
    if pd.notna(emp_id_num):
        rec = df_geo[pd.to_numeric(df_geo["id_empreendimento"], errors="coerce") == emp_id_num]
    else:
        rec = df_geo[df_geo["id_empreendimento"].astype(str) == str(empreendimento_id)]

    if rec.empty:
        _render_no_geometry_placeholder("Geometria não cadastrada para este empreendimento.")
        return

    row = rec.iloc[0]
    nome_emp = str(row.get("nome_empreendimento") or f"Empreendimento {empreendimento_id}")
    nome_safe = html_mod.escape(nome_emp)
    
    linha_wkt = row.get("geom_linha")
    ponto_wkt = row.get("geom_ponto")

    geom_linha = None
    geom_ponto = None
    geoms_valid = []

    # Carrega geometria de linha
    if pd.notna(linha_wkt) and str(linha_wkt).strip():
        try:
            geom_linha = wkt.loads(str(linha_wkt))
            if not geom_linha.is_empty:
                geoms_valid.append(geom_linha)
        except Exception:
            pass

    # Carrega geometria de ponto
    if pd.notna(ponto_wkt) and str(ponto_wkt).strip():
        try:
            geom_ponto = wkt.loads(str(ponto_wkt))
            if not geom_ponto.is_empty:
                geoms_valid.append(geom_ponto)
        except Exception:
            pass

    # Se não houver nenhuma geometria válida
    if not geoms_valid:
        _render_no_geometry_placeholder("Traçado geoespacial ainda não vetorizado para este empreendimento.")
        return

    # Calcula os limites (bounds)
    min_lon, min_lat, max_lon, max_lat = get_combined_bounds(geoms_valid)

    # Coordenada central padrão de Minas Gerais caso limites sejam pontuais
    center_lat = (min_lat + max_lat) / 2 if min_lat != float("inf") else -18.5
    center_lon = (min_lon + max_lon) / 2 if min_lon != float("inf") else -44.5

    # Cria o mapa base com OpenStreetMap (100% gratuito, aberto e sem necessidade de chave de API)
    m = folium.Map(
        location=[center_lat, center_lon],
        zoom_start=7,
        tiles="OpenStreetMap",
        control_scale=True,
    )

    # 1. Adiciona Intervenções Lineares
    if geom_linha and not geom_linha.is_empty:
        folium.GeoJson(
            geom_linha.__geo_interface__,
            name="Intervenção Linear",
            style_function=lambda x: {
                "color": "#1a5276",
                "weight": 4.5,
                "opacity": 0.90,
            },
            tooltip=f"<b>{nome_safe}</b><br>Intervenção Linear",
        ).add_to(m)

    # 2. Adiciona Intervenções Pontuais
    if geom_ponto and not geom_ponto.is_empty:
        folium.GeoJson(
            geom_ponto.__geo_interface__,
            name="Intervenção Pontual",
            marker=folium.CircleMarker(
                radius=6,
                color="#0b2545",
                fill=True,
                fill_color="#3b82f6",
                fill_opacity=0.90,
                weight=1.5,
            ),
            tooltip=f"<b>{nome_safe}</b><br>Intervenção Pontual",
        ).add_to(m)

    # Ajusta o zoom para enquadrar todo o traçado
    if min_lat != float("inf") and max_lat != float("-inf"):
        # Se for um único ponto, define limites com pequena margem
        if min_lat == max_lat and min_lon == max_lon:
            m.fit_bounds([[min_lat - 0.05, min_lon - 0.05], [max_lat + 0.05, max_lon + 0.05]])
        else:
            m.fit_bounds([[min_lat, min_lon], [max_lat, max_lon]], padding=(25, 25))

    # Renderiza o mapa no container do Streamlit (510 + 10 = 520px, alinhamento exato com os metadados)
    folium_static(m, height=510, width=None)


def _render_no_geometry_placeholder(mensagem: str):
    """Renderiza um cartão informativo quando o empreendimento não possui geometria."""
    st.markdown(
        f"""
        <div style="
            background: #f8fafc;
            border: 2px dashed #cbd5e1;
            border-radius: 10px;
            height: 520px;
            min-height: 520px;
            box-sizing: border-box;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            color: #64748b;
            font-size: 0.92rem;
            text-align: center;
            padding: 1.5rem;
        ">
            <span style="font-size: 2rem; margin-bottom: 0.5rem;">🗺️</span>
            <b>{html_mod.escape(mensagem)}</b>
        </div>
        """,
        unsafe_allow_html=True,
    )

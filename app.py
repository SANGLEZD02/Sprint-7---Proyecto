from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st


@st.cache_data
def load_data():
    data_path = Path(__file__).resolve().parent / "vehicles_us.csv"
    data = pd.read_csv(data_path, parse_dates=["date_posted"])
    data["is_4wd"] = data["is_4wd"].fillna(0).astype("int8")
    data["model_year"] = data["model_year"].astype("Int64")
    data["manufacturer"] = data["model"].str.split().str[0]
    data["age"] = data["date_posted"].dt.year - data["model_year"]

    price_limit = data["price"].quantile(0.99)
    filtered_data = data[data["price"].between(500, price_limit)].copy()
    return data, filtered_data, price_limit


st.set_page_config(page_title="Anuncios de coches", layout="wide")
st.title("Visualización de anuncios de venta de coches")

car_data, filtered_data, price_limit = load_data()

total_col, filtered_col, limit_col = st.columns(3)
total_col.metric("Anuncios analizados", f"{len(car_data):,}")
filtered_col.metric("Anuncios sin extremos de precio", f"{len(filtered_data):,}")
limit_col.metric("Percentil 99 del precio", f"${price_limit:,.0f}")
st.caption(
    "Los gráficos que indican «sin valores atípicos» usan anuncios con precios "
    "entre $500 y el percentil 99, siguiendo el criterio del notebook EDA."
)

charts = {
    "Valores ausentes": "missing",
    "Distribución del precio": "price",
    "Distribución del precio (sin valores atípicos)": "filtered_price",
    "Distribución del odómetro": "odometer",
    "Distribución del año del modelo": "model_year",
    "Días que el anuncio estuvo publicado": "days_listed",
    "Anuncios por tipo de vehículo": "type_counts",
    "Anuncios por fabricante": "manufacturer_counts",
    "Tipos de vehículo por fabricante": "manufacturer_type",
    "Condición según el año del modelo": "condition_year",
    "Precio vs. odómetro": "price_odometer",
    "Precio según la condición": "price_condition",
    "Precio según el tipo de vehículo": "price_type",
    "Precio mediano por año del modelo": "median_price_year",
    "Precio según combustible y transmisión": "price_fuel_transmission",
    "Matriz de correlación": "correlation",
}
selected_chart = st.selectbox("Selecciona un gráfico", list(charts))
chart = charts[selected_chart]
condition_order = ["new", "like new", "excellent", "good", "fair", "salvage"]

if chart == "missing":
    missing = (car_data.isna().mean() * 100).sort_values(ascending=False)
    missing = missing[missing > 0].rename_axis("columna").reset_index(name="porcentaje")
    fig = px.bar(
        missing,
        x="columna",
        y="porcentaje",
        text="porcentaje",
        title="Porcentaje de valores ausentes por columna",
        labels={"porcentaje": "% ausente", "columna": ""},
    )
elif chart == "price":
    fig = px.histogram(
        car_data,
        x="price",
        nbins=200,
        title="Distribución del precio",
        labels={"price": "Precio (USD)", "count": "Número de anuncios"},
    )
elif chart == "filtered_price":
    fig = px.histogram(
        filtered_data,
        x="price",
        nbins=60,
        marginal="box",
        title="Distribución del precio (sin valores atípicos)",
        labels={"price": "Precio (USD)", "count": "Número de anuncios"},
    )
elif chart == "odometer":
    fig = px.histogram(
        filtered_data,
        x="odometer",
        nbins=80,
        marginal="box",
        title="Distribución del odómetro (millas)",
        labels={"odometer": "Millas", "count": "Número de anuncios"},
    )
elif chart == "model_year":
    fig = px.histogram(
        filtered_data,
        x="model_year",
        title="Distribución del año del modelo",
        labels={"model_year": "Año del modelo", "count": "Número de anuncios"},
    )
elif chart == "days_listed":
    fig = px.histogram(
        filtered_data,
        x="days_listed",
        nbins=60,
        marginal="box",
        title="Días que el anuncio estuvo publicado",
        labels={"days_listed": "Días publicados", "count": "Número de anuncios"},
    )
elif chart == "type_counts":
    type_counts = car_data["type"].value_counts().rename_axis("type").reset_index(name="count")
    fig = px.bar(
        type_counts,
        x="type",
        y="count",
        title="Anuncios por tipo de vehículo",
        labels={"type": "", "count": "Número de anuncios"},
    )
elif chart == "manufacturer_counts":
    manufacturer_counts = (
        car_data["manufacturer"]
        .value_counts()
        .rename_axis("manufacturer")
        .reset_index(name="count")
    )
    fig = px.bar(
        manufacturer_counts,
        x="manufacturer",
        y="count",
        title="Anuncios por fabricante",
        labels={"manufacturer": "", "count": "Número de anuncios"},
    )
elif chart == "manufacturer_type":
    fig = px.histogram(
        car_data,
        x="manufacturer",
        color="type",
        barmode="stack",
        title="Tipos de vehículo por fabricante",
        labels={"manufacturer": "", "count": "Número de anuncios"},
        category_orders={"manufacturer": car_data["manufacturer"].value_counts().index.tolist()},
    )
    fig.update_layout(xaxis={"categoryorder": "total descending"})
elif chart == "condition_year":
    fig = px.histogram(
        car_data,
        x="model_year",
        color="condition",
        barmode="stack",
        category_orders={"condition": condition_order},
        title="Condición del vehículo según el año del modelo",
        labels={"model_year": "Año del modelo", "count": "Número de anuncios"},
    )
elif chart == "price_odometer":
    fig = px.scatter(
        filtered_data,
        x="odometer",
        y="price",
        color="condition",
        opacity=0.4,
        category_orders={"condition": condition_order},
        title="Precio vs. odómetro",
        labels={"odometer": "Millas", "price": "Precio (USD)"},
    )
elif chart == "price_condition":
    fig = px.box(
        filtered_data,
        x="condition",
        y="price",
        category_orders={"condition": condition_order},
        title="Precio según la condición",
        labels={"condition": "", "price": "Precio (USD)"},
    )
elif chart == "price_type":
    fig = px.box(
        filtered_data,
        x="type",
        y="price",
        title="Precio según el tipo de vehículo",
        labels={"type": "", "price": "Precio (USD)"},
    )
    fig.update_layout(xaxis={"categoryorder": "median descending"})
elif chart == "median_price_year":
    price_by_year = (
        filtered_data.groupby("model_year", as_index=False)["price"]
        .median()
        .query("model_year >= 1990")
    )
    fig = px.line(
        price_by_year,
        x="model_year",
        y="price",
        markers=True,
        title="Precio mediano por año del modelo (desde 1990)",
        labels={"model_year": "Año del modelo", "price": "Precio mediano (USD)"},
    )
elif chart == "price_fuel_transmission":
    fig = px.box(
        filtered_data,
        x="fuel",
        y="price",
        color="transmission",
        title="Precio según combustible y transmisión",
        labels={"fuel": "", "price": "Precio (USD)"},
    )
else:
    correlation_columns = [
        "price",
        "model_year",
        "age",
        "odometer",
        "cylinders",
        "is_4wd",
        "days_listed",
    ]
    correlation = filtered_data[correlation_columns].corr().round(2)
    fig = px.imshow(
        correlation,
        text_auto=True,
        color_continuous_scale="RdBu_r",
        zmin=-1,
        zmax=1,
        title="Matriz de correlación",
    )

st.plotly_chart(fig, width="stretch")

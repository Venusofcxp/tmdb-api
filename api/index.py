from fastapi import FastAPI
import requests

app = FastAPI(
    title="TMDB Viewer API",
    version="1.1",
    description="API personalizada para exibir filmes e séries do TMDB, incluindo episódios recentes e detalhes completos."
)

API_KEY = "95c54f7136073fc40e81f7ecd6a974e5"
BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p/w500"

# Função auxiliar para formatar resultados
def formatar_lista(dados):
    resultados = []
    for item in dados:
        resultados.append({
            "id": item.get("id"),
            "titulo": item.get("title") or item.get("name"),
            "sinopse": item.get("overview"),
            "nota": item.get("vote_average"),
            "data_lancamento": item.get("release_date") or item.get("first_air_date"),
            "poster": f"{IMG_BASE}{item['poster_path']}" if item.get("poster_path") else None,
            "fundo": f"{IMG_BASE}{item['backdrop_path']}" if item.get("backdrop_path") else None,
            "tipo": item.get("media_type", "movie")
        })
    return resultados


# 🔥 Tendência do dia ou semana
@app.get("/api/trending/{periodo}")
def trending(periodo: str):
    if periodo not in ["hoje", "semana"]:
        return {"erro": "Use 'hoje' ou 'semana'."}
    caminho = "day" if periodo == "hoje" else "week"
    url = f"{BASE_URL}/trending/all/{caminho}?api_key={API_KEY}&language=pt-BR"
    r = requests.get(url).json()
    return formatar_lista(r.get("results", []))


# 🎬 Filmes (populares, lançamentos, top, cartaz)
@app.get("/api/filmes/{categoria}")
def filmes(categoria: str):
    categorias = {
        "populares": "popular",
        "lancamentos": "upcoming",
        "melhores": "top_rated",
        "cartaz": "now_playing"
    }
    if categoria not in categorias:
        return {"erro": "Categoria inválida."}
    url = f"{BASE_URL}/movie/{categorias[categoria]}?api_key={API_KEY}&language=pt-BR"
    r = requests.get(url).json()
    return formatar_lista(r.get("results", []))


# 📺 Séries (populares, melhores, no ar)
@app.get("/api/series/{categoria}")
def series(categoria: str):
    categorias = {
        "populares": "popular",
        "melhores": "top_rated",
        "cartaz": "on_the_air"
    }
    if categoria not in categorias:
        return {"erro": "Categoria inválida."}
    url = f"{BASE_URL}/tv/{categorias[categoria]}?api_key={API_KEY}&language=pt-BR"
    r = requests.get(url).json()
    return formatar_lista(r.get("results", []))


# 🎥 Detalhes completos de filme
@app.get("/api/filme/{id}")
def filme_detalhe(id: int):
    url = f"{BASE_URL}/movie/{id}?api_key={API_KEY}&language=pt-BR&append_to_response=recommendations,release_dates"
    dados = requests.get(url).json()

    # Pega classificação etária (se disponível)
    classificacao = None
    if "release_dates" in dados:
        for regiao in dados["release_dates"].get("results", []):
            if regiao.get("iso_3166_1") == "BR":
                for rel in regiao.get("release_dates", []):
                    classificacao = rel.get("certification")
                    break

    return {
        "id": dados.get("id"),
        "titulo": dados.get("title"),
        "sinopse": dados.get("overview"),
        "nota": dados.get("vote_average"),
        "poster": f"{IMG_BASE}{dados['poster_path']}" if dados.get("poster_path") else None,
        "fundo": f"{IMG_BASE}{dados['backdrop_path']}" if dados.get("backdrop_path") else None,
        "data_lancamento": dados.get("release_date"),
        "duracao": dados.get("runtime"),
        "classificacao": classificacao or "N/A",
        "generos": [g["name"] for g in dados.get("genres", [])],
        "recomendacoes": formatar_lista(dados.get("recommendations", {}).get("results", []))
    }


# 📺 Detalhes completos de série
@app.get("/api/serie/{id}")
def serie_detalhe(id: int):
    url = f"{BASE_URL}/tv/{id}?api_key={API_KEY}&language=pt-BR&append_to_response=recommendations,content_ratings"
    dados = requests.get(url).json()

    # Classificação indicativa
    classificacao = None
    if "content_ratings" in dados:
        for regiao in dados["content_ratings"].get("results", []):
            if regiao.get("iso_3166_1") == "BR":
                classificacao = regiao.get("rating")
                break

    return {
        "id": dados.get("id"),
        "titulo": dados.get("name"),
        "sinopse": dados.get("overview"),
        "nota": dados.get("vote_average"),
        "poster": f"{IMG_BASE}{dados['poster_path']}" if dados.get("poster_path") else None,
        "fundo": f"{IMG_BASE}{dados['backdrop_path']}" if dados.get("backdrop_path") else None,
        "temporadas": dados.get("number_of_seasons"),
        "episodios": dados.get("number_of_episodes"),
        "ultimo_episodio": dados.get("last_episode_to_air"),
        "proximo_episodio": dados.get("next_episode_to_air"),
        "classificacao": classificacao or "N/A",
        "generos": [g["name"] for g in dados.get("genres", [])],
        "recomendacoes": formatar_lista(dados.get("recommendations", {}).get("results", []))
    }


# 🆕 Novos episódios lançados recentemente
@app.get("/api/series/novos_episodios")
def novos_episodios():
    url = f"{BASE_URL}/tv/changes?api_key={API_KEY}"
    changes = requests.get(url).json()

    recentes = []
    for item in changes.get("results", [])[:10]:  # Pega só os 10 mais recentes
        serie_id = item.get("id")
        detalhe_url = f"{BASE_URL}/tv/{serie_id}?api_key={API_KEY}&language=pt-BR"
        serie = requests.get(detalhe_url).json()
        ultimo = serie.get("last_episode_to_air")
        if ultimo:
            recentes.append({
                "serie_id": serie.get("id"),
                "titulo": serie.get("name"),
                "poster": f"{IMG_BASE}{serie['poster_path']}" if serie.get("poster_path") else None,
                "episodio_titulo": ultimo.get("name"),
                "episodio_sinopse": ultimo.get("overview"),
                "temporada": ultimo.get("season_number"),
                "episodio": ultimo.get("episode_number"),
                "data_lancamento": ultimo.get("air_date"),
                "nota": ultimo.get("vote_average", None)
            })

    return recentes

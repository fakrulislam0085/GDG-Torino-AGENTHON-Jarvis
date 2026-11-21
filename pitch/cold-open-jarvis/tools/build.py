import pathlib
R = pathlib.Path(__file__).resolve().parents[1]
src = (R / "tools/film.src.html").read_text(encoding="utf-8")
env = (R / "assets/audio/voice_env.json").read_text()
tiles = "".join('<div class="sn"></div>' for _ in range(40))
(R / "compositions/film.html").write_text(src.replace("__ENV__", env).replace("__TILES__", tiles), encoding="utf-8")

import pathlib
R = pathlib.Path(__file__).resolve().parents[1]
env = (R / "assets/audio/voice_env.json").read_text()
src = (R / "tools/film.src.html").read_text(encoding="utf-8")
(R / "compositions/film.html").write_text(src.replace("__ENV__", env), encoding="utf-8")

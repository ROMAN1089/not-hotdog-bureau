"""Original Gradio interface; pretrained model credited in README."""
import os
from functools import lru_cache

import gradio as gr
from PIL import ImageOps
from transformers import pipeline

MODEL = os.environ.get("HOTDOG_MODEL", "julien-c/hotdog-not-hotdog")


@lru_cache(maxsize=1)
def classifier():
    return pipeline("image-classification", model=MODEL, device=-1)


def inspect(image):
    if image is None:
        raise gr.Error("Сначала предъявите подозреваемого. Загрузите фото.")
    if image.width * image.height > 25_000_000:
        raise gr.Error("Фото слишком большое. Уменьшите его до 25 мегапикселей.")
    image = ImageOps.exif_transpose(image).convert("RGB")
    image.thumbnail((2048, 2048))
    try:
        predictions = classifier()(image, top_k=2)
    except Exception as exc:
        raise gr.Error("Инспектор недоступен. При первом запуске нужен интернет для загрузки модели. Проверьте подключение и попробуйте снова.") from exc
    scores = {p["label"]: float(p["score"]) for p in predictions}
    hotdog = next((v for k, v in scores.items() if k.lower().replace("_", " ").replace("-", " ").strip() == "hot dog"), None)
    if hotdog is None:
        raise gr.Error("Модель вернула неизвестные классы. Проверьте HOTDOG_MODEL.")
    if hotdog >= 0.5:
        title, detail, color = "🌭 HOT DOG", "Сосиска установлена. Инвестиционный раунд открыт.", "#c9ff55"
    else:
        title, detail, color = "🚫 NOT HOT DOG", "Это не хот-дог. На этом наши полномочия всё.", "#ff8072"
    verdict = f'<div class="verdict" style="border-color:{color}"><div class="stamp">ОФИЦИАЛЬНЫЙ ВЕРДИКТ</div><h1 style="color:{color}">{title}</h1><p>{detail}</p></div>'
    report = f"Вероятность класса «хот-дог»: {hotdog:.1%}. Это оценка модели, а не гарантия.\n\nНейросеть: {MODEL}\nМетод: анализ изображения. Дегустация не проводилась."
    return verdict, scores, report


CSS = """
.gradio-container {max-width:1100px!important;background:#101211!important;color:#f4f4eb!important}
.hero {padding:40px 12px 28px}.eyebrow,.stamp{font:12px monospace;letter-spacing:3px;color:#a7ad9c}
.hero h1{font-size:clamp(42px,7vw,82px);letter-spacing:-4px;line-height:1.05;margin:18px 0;color:#c9ff55}
.hero p{font-size:18px;color:#b7bead;max-width:680px}.verdict{min-height:190px;border:2px solid #3d4433;border-radius:18px;padding:26px;background:#171b14}
.verdict h1{font-size:44px;letter-spacing:-2px}.verdict p{font-size:18px}.footer{padding:22px 8px;color:#929988;font:12px monospace}
#inspect-button{background:#c9ff55!important;color:#101211!important;border:0;font-weight:800;font-size:18px;min-height:60px}
"""


def build_app():
    with gr.Blocks(title="Not Hotdog — Бюро сосисок", css=CSS, theme=gr.themes.Base()) as app:
        gr.HTML('<div class="hero"><div class="eyebrow">БЮРО КОНТРОЛЯ СОСИСОК / EST. 2026</div><h1>Один вопрос.<br>Ноль амбиций.</h1><p>В мире, где ИИ пишет диссертации, мы выясняем главное: это хот-дог?</p></div>')
        with gr.Row():
            with gr.Column():
                image = gr.Image(type="pil", sources=["upload", "webcam"], label="Предъявите подозреваемого", height=330)
                button = gr.Button("ПРОВЕРИТЬ СОСИСКУ →", elem_id="inspect-button")
            with gr.Column():
                verdict = gr.HTML('<div class="verdict"><div class="stamp">ДЕЛО НЕ ОТКРЫТО</div><h1>🌭 или 🚫?</h1><p>Ждём фото. Эксперт разогревается.</p></div>')
                scores = gr.Label(label="Показания нейросети", num_top_classes=2)
                report = gr.Textbox(label="Протокол проверки", lines=4, interactive=False)
        button.click(inspect, image, [verdict, scores, report], api_name="inspect")
        gr.HTML('<div class="footer">НЕЗАВИСИМЫЙ ФАН-ПРОЕКТ · НЕ СВЯЗАН С HBO · MODEL: JULIEN-C/HOTDOG-NOT-HOTDOG<br>Фото обрабатывается на компьютере, где запущено приложение. Модель загружается с Hugging Face при первом запуске.</div>')
    return app


if __name__ == "__main__":
    build_app().queue().launch(server_name="127.0.0.1", server_port=int(os.environ.get("PORT", "7860")))

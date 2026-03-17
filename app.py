from playwright.sync_api import sync_playwright
from dotenv import load_dotenv
import os
import openai

load_dotenv(override=True)
openai.api_key = os.getenv("OPENAI_API_KEY")

SUBJECTS_FILE = "C:/Users/AMD/Documents/Projetos VScode/EJAFlux/subjects_links.txt"
CLASSES_FILE = "C:/Users/AMD/Documents/Projetos VScode/EJAFlux/classes_links.txt"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    context = browser.new_context()
    page = context.new_page()

    def login():
        page.locator('xpath=//*[@id="email"]').fill(os.getenv("USERNAME"))
        page.locator('xpath=//*[@id="password"]').fill(os.getenv("PASSWORD"))
        page.locator('xpath=/html/body/main/div/div/div/div[2]/div/div[2]/form/button').click()

    def subjects():
        subjects_page = context.new_page()
        subjects_page.goto(os.getenv("URL_SITE"))
        subjects_page.locator('xpath=//*[@id="email"]').fill(os.getenv("USERNAME"))
        subjects_page.locator('xpath=//*[@id="password"]').fill(os.getenv("PASSWORD"))
        subjects_page.locator('xpath=/html/body/main/div/div/div/div[2]/div/div[2]/form/button').click()
        subjects_page.wait_for_load_state('networkidle')

        hrefs = subjects_page.eval_on_selector_all(
            "a[href*='fazercurso.php?id=']",
            "elements => elements.map(e => e.href)"
        )
        fixed_hrefs = list(set(hrefs))

        with open(SUBJECTS_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_hrefs))

        subjects_page.close()

    def get_aulas():
        hrefs = page.eval_on_selector_all(
            "a[href*='fazeraula.php?id=']",
            "elements => elements.map(e => e.href)"
        )
        fixed_hrefs = list(set(hrefs))
        with open(CLASSES_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(fixed_hrefs))

    def begin_questions():
        page.locator('xpath=/html/body/div/div[4]/div/div/div/div[1]/button[2]').click()

    def yes_button():
        page.locator('xpath=/html/body/div[1]/div[4]/div/div/div/div[1]/div[1]/div/div/div[3]/a/button').click()

    def get_question():
        pergunta = page.locator('xpath=/html/body/div/div[4]/div/div/div/div[1]/form/div[1]/div').text_content()
        opcoes_elements = page.locator('#custom-control-label')
        opcoes = [e.text_content() for e in opcoes_elements.all()]
        
        prompt = f"Pergunta: {pergunta}\nOpções:\n" + "\n".join(opcoes) + "\nQual é a resposta correta?"
        
        resposta = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=50
        )

        resposta_certa = resposta['choices'][0]['message']['content']
        print("Pergunta:", pergunta)
        print("Opções:", opcoes)
        print("Resposta sugerida pelo GPT:", resposta_certa)
        return resposta_certa

    def next_finish_question():
        page.locator('xpath=//*[@id="proxima"]').click()

    def responder_questionario(qtd=5):
        try:
            begin_questions()
            yes_button()
        except:
                try:
                    page.locator('xpath=/html/body/div/div[4]/div/div/div/div[1]/button[2]').click()
                except:
                    pass

                    contador = 0
                    while contador < qtd:
                        get_question()
                        next_finish_question()
                        contador += 1

    page.goto(os.getenv("URL_SITE"))
    login()

    with open(SUBJECTS_FILE, "r", encoding="utf-8") as f:
        materias = [linha.strip() for linha in f if linha.strip()]

    for materia in materias:
        page.goto(materia)
        get_aulas()

        with open(CLASSES_FILE, "r", encoding="utf-8") as f:
            aulas = [linha.strip() for linha in f if linha.strip()]

        for aula in aulas:
            page.goto(aula)
            responder_questionario()

    browser.close()
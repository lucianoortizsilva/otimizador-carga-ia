from transformers import pipeline

geradorTexto = pipeline("text-generation", model="pierreguillou/gpt2-small-portuguese")
texto = "O sport club internacional, clube de futebol foi fundado em 04 abril de 1909. Localizado na capital gaúcha de Porto Alegre, no estado do Rio Grande do Sul - Brasil"
print(geradorTexto(texto, max_length=100, do_sample=True))
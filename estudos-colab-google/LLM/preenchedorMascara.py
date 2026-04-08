from transformers import pipeline
mascarar = pipeline('fill-mask', model='neuralmind/bert-base-portuguese-cased')
texto = mascarar('Pelé é o rei do [MASK]')
for x in range(len(texto)):
  print(texto[x])
from transformers import pipeline

resumir = pipeline(task="summarization",  model="Falconsai/text_summarization")

texto = """
Prison Break is an American crime drama television series created by Paul Scheuring for Fox. The series revolves around two brothers: Lincoln Burrows (Dominic Purcell) and Michael Scofield (Wentworth Miller); Lincoln has been sentenced to death for a crime he did not commit, while Michael devises an elaborate plan to help his brother escape prison and clear his name. Along with creator Paul Scheuring, the series was executive-produced by Matt Olmstead, Kevin Hooks, Marty Adelstein, Dawn Parouse, Neal H. Moritz, and Brett Ratner who directed the pilot episode. The series' theme music, composed by Ramin Djawadi, was nominated for a Primetime Emmy Award in 2006.[1] Prison Break is a joint production between Original Film, Adelstein/Parouse Productions (seasons 1–4), Dawn Olmstead Productions (season 5), Adelstein Productions (season 5), One Light Road Productions (season 5), and 20th Century Fox Television.
The series was originally turned down by Fox in 2003, which was concerned about the long-term prospects of such a series. Following the popularity of serialized prime time television series 24 and Lost, Fox decided to back production in 2004. The first season received mostly positive reviews from critics.[2] Furthermore, it performed exceptionally in these ratings and was originally planned for a 13-episode run, but was extended to include an extra nine episodes due to its popularity. The subsequent seasons continued to receive strong ratings; however some critics claimed the show had overstayed its welcome.[3] Prison Break was nominated for several industry awards, including the 2005 Golden Globe Award for Best Television Series Drama and the 2006 People's Choice Award for Favorite New TV Drama, which it won. In the United States, all five seasons have been released on DVD and released on Blu-ray internationally.
"""

resumo = resumir(texto, max_length=100, min_length=50, do_sample=False)

print(resumo)
#
# from ibm_watson import ToneAnalyzerV3
#
#
# def text_tone_analysis(text):
#     tone_analyzer = ToneAnalyzerV3(
#         version='2017-09-21',
#         iam_apikey='vUuPgM6ykSwsTff-C8KeYccnu4zu_BSM4yJf0WHXSKYK',
#         url='https://gateway-lon.watsonplatform.net/tone-analyzer/api'
#     )
#
#     tone_ids = ['anger', 'fear', 'joy', 'sadness', 'analytical', 'confident', 'tentative']
#     get_symbol = {
#         "anger": "angry_face",
#         "fear": "fear_face",
#         "joy": "joy_face",
#         "sadness": "sadness_face",
#         "analytical": "analytical_face",
#         "confident": "confident_face"
#     }
#
#     tone_analysis = tone_analyzer.tone(
#         tone_input=text
#     ).get_result()
#
#     # print(json.dumps(tone_analysis, indent=2))
#
#     res = {}
#     for tone_category in tone_analysis["document_tone"]["tones"]:
#         res[tone_category["score"]] = tone_category
#
#     if res:
#         return res[max(res.keys())]
#     else:
#         raise Exception
#
#
# text = "Happy to see you"
# print(text_tone_analysis(text))

def prompt_gen(question, reference):
    prompt = f"""<|begin_of_text|><|start_header_id|>system<|end_header_id|> You will recieve, HR POLICY, and user's question, QUESTION, inside ''' below. Please answer the question in Thai language
'''
HR POLICY: {reference}
QUESTION: {question}
'''
Answer the question using the HR POLICY if the question is irrelevant to the HR POLICY please say
“ฉันไม่ทราบคำตอบ ไม่ได้เป็นส่วนหนึ่งของเอกสาร HR POLICY ที่ให้มา”
Don't use any information outside the provided policy.
Answer the question in Thai.<|eot_id|>
<|start_header_id|>user<|end_header_id|> คำถาม: {question} <|eot_id|>
<|start_header_id|>assistant<|end_header_id|> คำตอบ:"""
    return prompt
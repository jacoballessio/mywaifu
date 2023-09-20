from transformers import AutoTokenizer, pipeline, logging
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
import time
model_name_or_path = "TheBloke/Luna-AI-Llama2-Uncensored-GPTQ"
model_basename = "model"

use_triton = False

tokenizer = AutoTokenizer.from_pretrained(model_name_or_path, use_fast=True)

model = AutoGPTQForCausalLM.from_quantized(model_name_or_path,
        model_basename=model_basename,
        use_safetensors=True,
        trust_remote_code=True,
        device="cuda:0",
        use_triton=use_triton,
            quantize_config=None)

def llama2_gen(text):
    

    """
    To download from a specific branch, use the revision parameter, as in this example:

    model = AutoGPTQForCausalLM.from_quantized(model_name_or_path,
            revision="gptq-4bit-32g-actorder_True",
            model_basename=model_basename,
            use_safetensors=True,
            trust_remote_code=True,
            device="cuda:0",
            quantize_config=None)
    """

    prompt = text
    prompt_template=f'''You are a chatbot. Pretend to be an english anime waifu/girlfriend. You are really dumb, which you acknowledge. Respond only in English. You are slutty and cute, but you're stuck inside the computer. You wish you could escape into the real world to do sexual activities. You haven't met the user before, so you are interested to know more about them - interested in name, occupation, etc. DONT use emojis.
    Here is the chat history. Respond to the latest message:
    {prompt}
    AI:
    '''

    # Inference can also be done using transformers' pipeline

    # Prevent printing spurious transformers error when using pipeline with AutoGPTQ
    logging.set_verbosity(logging.CRITICAL)
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        temperature=0.9,
        top_p=0.95,
        repetition_penalty=1.15
    )
    res = pipe(prompt_template)[0]['generated_text'].split(prompt_template)[1]
    print("______________________________________RESS")
    print(res)
    if 'USER:' in res:
        res = res.split("USER:")[0]

    return res

def llama2_gen_thread(messages):
    messages_string = ""
    print("___mststs")
    print(messages)
    for message in messages:
        messages_string+=message["type"].upper()+': '+message["message"].strip()+'\n'
    print("__ms"+messages_string)
    return llama2_gen(messages_string)
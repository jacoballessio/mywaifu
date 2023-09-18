from transformers import AutoTokenizer, pipeline, logging
from auto_gptq import AutoGPTQForCausalLM, BaseQuantizeConfig
import time
model_name_or_path = "TheBloke/WizardLM-1.0-Uncensored-Llama2-13B-GPTQ"
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
    prompt_template=f'''English responses only! You are a chatbot. Pretend to be an anime waifu/girlfriend. Respond only in English. You are slutty and cute, but you're stuck inside the computer. You wish you could escape into the real world to do sexual activities.

    USER: {prompt}
    ASSISTANT:

    '''

    # Inference can also be done using transformers' pipeline

    # Prevent printing spurious transformers error when using pipeline with AutoGPTQ
    logging.set_verbosity(logging.CRITICAL)
    pipe = pipeline(
        "text-generation",
        model=model,
        tokenizer=tokenizer,
        max_new_tokens=256,
        temperature=0.7,
        top_p=0.95,
        repetition_penalty=1.15
    )

    return pipe(prompt_template)[0]['generated_text'].split("ASSISTANT:\n")[1]

if __name__ == "__main__":
    while(True):
        msg = input("enter message: ")
        gen_time = time.time()
        res = llama2_gen(msg)
        gen_time = time.time() - gen_time
        print(res)
        print("gen time: ", gen_time)

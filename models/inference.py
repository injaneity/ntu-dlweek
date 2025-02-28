# load the finetuned hatebert and test it on some samples
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = "./hatebert_finetuned"
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

def predict_hate_speech(input_text: str) -> dict:
    # tokenise the input text -- the same settings as during training -- impt
    inputs = tokenizer(
        input_text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=128
    )
    
    # inference, forward pass, no gradient tracking
    with torch.no_grad():
        outputs = model(**inputs)
    
    # get absolute outputs
    logits = outputs.logits
    probabilities = torch.softmax(logits, dim=1).tolist()[0]
    predicted_class = int(torch.argmax(logits, dim=1).item())
    
    label_mapping = {0: "non-hate", 1: "hate"}
    
    return {
        "input_text": input_text,
        "predicted_class": predicted_class,
        "label": label_mapping.get(predicted_class, "unknown"),
        "probabilities": probabilities,
    }

if __name__ == "__main__":
    # examples, use same one if you wanna test
    sample_texts = [
        "I love this community and how supportive it is.",
        "This group of people is absolutely worthless and should be banned.",
        "What a beautiful day!",
        "I hate these idiots, they ruin everything."
    ]
    
    for text in sample_texts:
        result = predict_hate_speech(text)
        print("Input Text:", result["input_text"])
        print("Predicted Label:", result["label"])
        print("Probabilities:", result["probabilities"])
        print("-" * 50)
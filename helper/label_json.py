import json
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification

MODEL_DIR = "../models/tuned_model/"
tokenizer = AutoTokenizer.from_pretrained(MODEL_DIR)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_DIR)

def predict_label(text: str) -> int:
    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding="max_length",
        max_length=128
    )
    with torch.no_grad():
        outputs = model(**inputs)
    
    logits = outputs.logits
    predicted_class = int(torch.argmax(logits, dim=1).item())  # 0 or 1
    return predicted_class

def main():
    with open("../data/input_data.json", "r", encoding="utf-8") as f:
        data_list = json.load(f)  # data_list is a list of dicts
    
    # for each JSON object, extract the text and predict the label
    for item in data_list:
        # The text is stored at item["record"]["text"]
        text = item["record"]["text"]
        
        # predict label (0 for non-hate and 1 for hate) with finetuned model
        predicted_class = predict_label(text)
        
        # insert a new field "label" into the JSON object
        item["label"] = predicted_class
    
    # create new file with labelled data
    with open("../output/labelled_data.json", "w", encoding="utf-8") as f:
        json.dump(data_list, f, indent=2, ensure_ascii=False)

if __name__ == "__main__":
    main()
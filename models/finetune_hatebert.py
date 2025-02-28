import os
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, Trainer, TrainingArguments
from datasets import load_dataset
import numpy as np
from sklearn.metrics import accuracy_score, f1_score

MODEL_NAME = "GroNLP/hateBERT"

tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=2)

data_files = {"data": "../data/balanced_train.csv"}
dataset = load_dataset("csv", data_files=data_files)
dataset = dataset["data"].train_test_split(test_size=0.2, seed=42)

dataset = dataset.filter(lambda example: example["Content"] is not None and example["Content"] != "")

def tokenize_function(examples):
    tokenized = tokenizer(
        examples["Content"],
        truncation=True,
        padding="max_length",
        max_length=128
    )
    tokenized["labels"] = examples["Label"]
    return tokenized

tokenized_datasets = dataset.map(tokenize_function, batched=True, remove_columns=["Content"])

# acc, f1
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    f1 = f1_score(labels, preds, average="weighted")
    return {"accuracy": acc, "f1": f1}

# training parameters -- lr at 2e-5, epochs at 3
training_args = TrainingArguments(
    output_dir="./hatebert_finetuned",
    evaluation_strategy="epoch",
    save_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=16,
    per_device_eval_batch_size=16,
    num_train_epochs=3,
    weight_decay=0.01,
    logging_dir="./logs",
    save_total_limit=2,
    load_best_model_at_end=True,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_datasets["train"],
    eval_dataset=tokenized_datasets["test"],
    compute_metrics=compute_metrics,
)

def main():
    trainer.train()

    # REMEMBER TO SAVE THE MODEL
    trainer.save_model("./hatebert_finetuned")
    tokenizer.save_pretrained("./hatebert_finetuned")
    print("Model fine-tuning complete and saved to './hatebert_finetuned'.")

if __name__ == "__main__":
    main()